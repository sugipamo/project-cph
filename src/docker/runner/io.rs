use bollard::exec::CreateExecOptions;
use futures::StreamExt;
use tokio::time::timeout;

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

        tokio::spawn(async move {
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
                            cmd: Some(vec!["sh", "-c", &format!("echo '{}' | tee /dev/stdin", input)]),
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

                match timeout(timeout_duration, docker.start_exec(&exec.id, None)).await {
                    Ok(Ok(bollard::exec::StartExecResults::Attached { mut output, .. })) => {
                        while let Some(Ok(output)) = output.next().await {
                            match output {
                                bollard::container::LogOutput::StdOut { message } => {
                                    let mut stdout = stdout_buffer.lock().await;
                                    stdout.push(String::from_utf8_lossy(&message).to_string());
                                }
                                bollard::container::LogOutput::StdErr { message } => {
                                    let mut stderr = stderr_buffer.lock().await;
                                    stderr.push(String::from_utf8_lossy(&message).to_string());
                                }
                                _ => {}
                            }
                        }
                    }
                    _ => {
                        *state.lock().await = RunnerState::Error;
                        break;
                    }
                }
            }
        });

        Ok(())
    }
} 