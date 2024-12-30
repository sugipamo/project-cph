use bollard::exec::{CreateExecOptions, StartExecResults};
use futures::StreamExt;

use crate::docker::state::RunnerState;
use crate::config::languages::RunnerInfo;
use super::DockerRunner;

impl DockerRunner {
    pub(super) async fn compile(&mut self, lang_config: RunnerInfo) -> () {
        if let Some(compile_cmd) = &lang_config.compile {
            let exec = match self.docker
                .create_exec(
                    &self.container_id,
                    CreateExecOptions {
                        cmd: Some(compile_cmd.clone()),
                        working_dir: Some(lang_config.compile_dir.to_string()),
                        ..Default::default()
                    },
                )
                .await {
                    Ok(exec) => exec,
                    Err(e) => {
                        println!("Failed to create exec: {:?}", e);
                        return;
                    }
                };

            match self.docker.start_exec(&exec.id, None).await {
                Ok(StartExecResults::Attached { mut output, .. }) => {
                    while let Some(Ok(output)) = output.next().await {
                        if let bollard::container::LogOutput::StdErr { message } = output {
                            let mut stderr = self.stderr_buffer.lock().await;
                            stderr.push(String::from_utf8_lossy(&message).to_string());
                        }
                    }
                }
                Ok(_) => {
                    println!("Compilation failed: unexpected exec result");
                    return;
                }
                Err(e) => {
                    println!("Failed to start exec: {:?}", e);
                    return;
                }
            }

            // コンパイルエラーをチェック
            let stderr = self.read_error().await;
            if !stderr.is_empty() {
                println!("Compilation error: {}", stderr);
                *self.state.lock().await = RunnerState::Error;
                return;
            }
        }
    }
} 