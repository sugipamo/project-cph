use bollard::exec::{CreateExecOptions, StartExecResults};
use futures::StreamExt;

use crate::docker::error::{DockerError, Result};
use crate::docker::state::RunnerState;
use crate::docker::config::LanguageConfig;
use super::DockerRunner;

impl DockerRunner {
    pub(super) async fn compile(&mut self, lang_config: LanguageConfig) -> Result<()> {
        if let Some(compile_cmd) = &lang_config.compile {
            let exec = self.docker
                .create_exec(
                    &self.container_id,
                    CreateExecOptions {
                        cmd: Some(compile_cmd.clone()),
                        working_dir: Some(lang_config.get_workspace_dir().to_string()),
                        ..Default::default()
                    },
                )
                .await
                .map_err(DockerError::ConnectionError)?;

            match self.docker.start_exec(&exec.id, None).await.map_err(DockerError::ConnectionError)? {
                StartExecResults::Attached { mut output, .. } => {
                    while let Some(Ok(output)) = output.next().await {
                        if let bollard::container::LogOutput::StdErr { message } = output {
                            let mut stderr = self.stderr_buffer.lock().await;
                            stderr.push(String::from_utf8_lossy(&message).to_string());
                        }
                    }
                }
                _ => return Err(DockerError::CompilationError("Compilation failed".to_string())),
            }

            // コンパイルエラーをチェック
            let stderr = self.read_error_all().await?;
            if !stderr.is_empty() {
                *self.state.lock().await = RunnerState::Error;
                return Err(DockerError::CompilationError(stderr.join("\n")));
            }
        }
        Ok(())
    }
} 