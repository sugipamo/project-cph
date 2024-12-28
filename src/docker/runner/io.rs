use bollard::exec::CreateExecOptions;
use futures::StreamExt;
use tokio::time::timeout;
use bollard::container::{LogsOptions, LogOutput};

use crate::docker::error::{DockerError, Result};
use crate::docker::state::RunnerState;
use super::DockerRunner;

#[derive(Debug)]
pub struct DockerOutput {
    pub stdout: String,
    pub stderr: String,
    pub execution_time: std::time::Duration,
}

impl DockerRunner {
    pub async fn write(&self, input: &str) -> Result<()> {
        let tx = self.stdin_tx.as_ref()
            .ok_or(DockerError::ContainerNotInitialized)?;

        tx.send(input.to_string())
            .await
            .map_err(|_| DockerError::RuntimeError("Failed to send input".to_string()))?;

        Ok(())
    }

    pub async fn read(&self) -> Result<String> {
        let stdout = self.stdout_buffer.lock().await;
        Ok(stdout.last()
            .cloned()
            .unwrap_or_default())
    }

    pub async fn read_error(&self) -> Result<String> {
        let stderr = self.stderr_buffer.lock().await;
        Ok(stderr.last()
            .cloned()
            .unwrap_or_default())
    }

    pub async fn read_all(&self) -> Result<Vec<String>> {
        let stdout = self.stdout_buffer.lock().await;
        Ok(stdout.clone())
    }

    pub async fn read_error_all(&self) -> Result<Vec<String>> {
        let stderr = self.stderr_buffer.lock().await;
        Ok(stderr.clone())
    }

    pub(crate) async fn setup_io(&mut self) -> Result<()> {
        let (tx, mut rx) = tokio::sync::mpsc::channel::<String>(32);
        self.stdin_tx = Some(tx);

        let container_id = self.container_id.clone();
        let docker = self.docker.clone();
        let stdout_buffer = self.stdout_buffer.clone();
        let stderr_buffer = self.stderr_buffer.clone();
        let state = self.state.clone();
        let timeout_duration = tokio::time::Duration::from_secs(self.config.timeout_seconds);

        // 入力と出力の処理を1つのタスクにまとめる
        tokio::spawn(async move {
            // 出力監視の設定
            let options: LogsOptions<String> = LogsOptions {
                follow: true,
                stdout: true,
                stderr: true,
                timestamps: false,
                ..Default::default()
            };

            let mut logs = docker.logs(&container_id, Some(options));

            // 出力監視のタスク
            let logs_task = tokio::spawn(async move {
                while let Some(Ok(output)) = logs.next().await {
                    match output {
                        LogOutput::StdOut { message } => {
                            let mut stdout = stdout_buffer.lock().await;
                            stdout.push(String::from_utf8_lossy(&message).trim().to_string());
                        }
                        LogOutput::StdErr { message } => {
                            let mut stderr = stderr_buffer.lock().await;
                            stderr.push(String::from_utf8_lossy(&message).trim().to_string());
                        }
                        _ => {}
                    }
                }
            });

            // 入力処理のタスク
            let input_task = tokio::spawn(async move {
                while let Some(input) = rx.recv().await {
                    if *state.lock().await != RunnerState::Running {
                        break;
                    }

                    let exec = match docker
                        .create_exec(
                            &container_id,
                            CreateExecOptions {
                                attach_stdin: Some(true),
                                attach_stdout: Some(true),
                                attach_stderr: Some(true),
                                cmd: Some(vec!["sh".to_string(), "-c".to_string(), format!("printf '%s' '{}' > /proc/1/fd/0", input.replace("'", "'\"'\"'"))]),
                                ..Default::default()
                            },
                        )
                        .await
                    {
                        Ok(exec) => exec,
                        Err(_) => {
                            *state.lock().await = RunnerState::Error;
                            break;
                        }
                    };

                    if let Err(_) = timeout(timeout_duration, docker.start_exec(&exec.id, None)).await {
                        *state.lock().await = RunnerState::Error;
                        break;
                    }
                }
            });

            // 両方のタスクが終了するまで待機
            tokio::select! {
                _ = logs_task => {},
                _ = input_task => {},
            }
        });

        Ok(())
    }
} 