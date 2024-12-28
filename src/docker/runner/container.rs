use bollard::container::{Config, CreateContainerOptions, StartContainerOptions};
use bollard::exec::{CreateExecOptions, StartExecResults};
use bollard::image::CreateImageOptions;
use futures::StreamExt;
use tokio::time::Duration;

use crate::docker::error::{DockerError, Result};
use crate::docker::state::RunnerState;
use super::DockerRunner;

impl DockerRunner {
    pub async fn initialize(&mut self, source_code: &str) -> Result<()> {
        let current_state = self.state.lock().await.clone();
        if current_state != RunnerState::Ready {
            return Err(DockerError::InvalidStateTransition {
                from: current_state.to_string(),
                to: RunnerState::Running.to_string(),
            });
        }

        let lang_config = self.config.get_language_config(&self.language)
            .ok_or_else(|| DockerError::UnsupportedLanguage(self.language.clone()))?;

        // イメージのプル
        let mut image_stream = self.docker.create_image(
            Some(CreateImageOptions {
                from_image: &lang_config.image_name,
                ..Default::default()
            }),
            None,
            None,
        );

        while let Some(result) = image_stream.next().await {
            result.map_err(DockerError::ConnectionError)?;
        }

        // コンテナの作成
        let mut cmd = lang_config.run_cmd.clone();
        cmd.push(source_code.to_string());

        let container = self.docker
            .create_container(
                Some(CreateContainerOptions { name: "" }),
                Config {
                    image: Some(&lang_config.image_name),
                    cmd: Some(cmd),
                    memory: Some(self.config.memory_limit_mb * 1024 * 1024),
                    working_dir: Some(&lang_config.workspace_dir),
                    tty: Some(true),
                    attach_stdin: Some(true),
                    attach_stdout: Some(true),
                    attach_stderr: Some(true),
                    open_stdin: Some(true),
                    ..Default::default()
                },
            )
            .await
            .map_err(DockerError::ConnectionError)?;

        self.container_id = container.id;

        // コンパイルが必要な場合は実行
        if let Some(compile_cmd) = &lang_config.compile_cmd {
            let exec = self.docker
                .create_exec(
                    &self.container_id,
                    CreateExecOptions {
                        cmd: Some(compile_cmd.iter().map(|s| s.as_str()).collect()),
                        working_dir: Some(&lang_config.workspace_dir),
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

        // コンテナの起動
        self.docker
            .start_container(&self.container_id, None::<StartContainerOptions<String>>)
            .await
            .map_err(DockerError::ConnectionError)?;

        // I/O設定
        self.setup_io().await?;

        *self.state.lock().await = RunnerState::Running;
        Ok(())
    }

    pub async fn stop(&mut self) -> Result<()> {
        let current_state = self.state.lock().await.clone();
        current_state.can_transition_to(&RunnerState::Stop)?;

        if !self.container_id.is_empty() {
            self.docker
                .stop_container(&self.container_id, None)
                .await
                .map_err(DockerError::ConnectionError)?;
        }

        *self.state.lock().await = RunnerState::Stop;
        Ok(())
    }
} 