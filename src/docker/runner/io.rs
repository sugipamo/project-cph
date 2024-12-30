use bollard::exec::CreateExecOptions;
use futures::StreamExt;
use tokio::time::timeout;
use bollard::container::{LogsOptions, LogOutput};
use std::time::Duration;

use crate::docker::error::{DockerError, Result};
use crate::docker::state::RunnerState;
use super::DockerRunner;

impl DockerRunner {
    pub async fn write(&self, input: &str) -> Result<()> {
        println!("Writing to container: {}", input);
        let tx = self.stdin_tx.as_ref()
            .ok_or_else(|| {
                println!("Container not initialized for writing");
                DockerError::ContainerNotInitialized
            })?;

        match tx.send(input.to_string()).await {
            Ok(_) => {
                println!("Successfully wrote to container");
                Ok(())
            }
            Err(e) => {
                println!("Failed to write to container: {:?}", e);
                Err(DockerError::RuntimeError("Failed to send input".to_string()))
            }
        }
    }

    pub async fn read(&self) -> Result<String> {
        println!("Attempting to read from container");
        let stdout = self.stdout_buffer.lock().await;
        match stdout.last() {
            Some(output) => {
                println!("Read from container: '{}'", output);
                Ok(output.clone())
            }
            None => {
                println!("No output available from container");
                Ok(String::new())
            }
        }
    }

    pub async fn read_error(&self) -> Result<String> {
        let stderr = self.stderr_buffer.lock().await;
        match stderr.last() {
            Some(error) => {
                println!("Read error from container: '{}'", error);
                Ok(error.clone())
            }
            None => {
                println!("No error output available from container");
                Ok(String::new())
            }
        }
    }

    pub(crate) async fn setup_io(&mut self) -> Result<()> {
        println!("Setting up I/O for container: {}", self.container_id);
        let (tx, mut rx) = tokio::sync::mpsc::channel::<String>(32);
        self.stdin_tx = Some(tx);

        let container_id = self.container_id.clone();
        let docker = self.docker.clone();
        let stdout_buffer = self.stdout_buffer.clone();
        let stderr_buffer = self.stderr_buffer.clone();
        let state = self.state.clone();
        let timeout_duration = Duration::from_secs(self.config.timeout_seconds);

        // 標準出力の監視
        let stdout_options = LogsOptions::<String> {
            follow: true,
            stdout: true,
            stderr: false,
            ..Default::default()
        };

        let stderr_options = LogsOptions::<String> {
            follow: true,
            stdout: false,
            stderr: true,
            ..Default::default()
        };

        // 標準出力の処理
        let stdout_container_id = container_id.clone();
        let mut stdout_stream = docker.logs(&stdout_container_id, Some(stdout_options));
        tokio::spawn(async move {
            while let Some(Ok(output)) = stdout_stream.next().await {
                if let LogOutput::StdOut { message } = output {
                    let output = String::from_utf8_lossy(&message).to_string();
                    println!("Container stdout: {}", output);
                    stdout_buffer.lock().await.push(output);
                }
            }
            println!("Stdout stream ended for container {}", stdout_container_id);
        });

        // 標準エラー出力の処理
        let stderr_container_id = container_id.clone();
        let mut stderr_stream = docker.logs(&stderr_container_id, Some(stderr_options));
        tokio::spawn(async move {
            while let Some(Ok(output)) = stderr_stream.next().await {
                if let LogOutput::StdErr { message } = output {
                    let error = String::from_utf8_lossy(&message).to_string();
                    println!("Container stderr: {}", error);
                    stderr_buffer.lock().await.push(error);
                }
            }
            println!("Stderr stream ended for container {}", stderr_container_id);
        });

        // 標準入力の処理
        let input_container_id = container_id.clone();
        let input_docker = docker.clone();
        tokio::spawn(async move {
            while let Some(input) = rx.recv().await {
                println!("Processing input: {}", input);
                match timeout(timeout_duration, async {
                    let exec = input_docker
                        .create_exec(
                            &input_container_id,
                            CreateExecOptions {
                                attach_stdin: Some(true),
                                attach_stdout: Some(true),
                                attach_stderr: Some(true),
                                cmd: Some(vec!["sh".to_string(), "-c".to_string(), format!("printf '%s' '{}' > /proc/1/fd/0", input.replace("'", "'\"'\"'"))]),
                                ..Default::default()
                            },
                        )
                        .await?;

                    input_docker.start_exec(&exec.id, None).await?;
                    Ok::<_, bollard::errors::Error>(())
                })
                .await
                {
                    Ok(Ok(_)) => println!("Successfully processed input"),
                    Ok(Err(e)) => {
                        println!("Error processing input: {:?}", e);
                        *state.lock().await = RunnerState::Error;
                    }
                    Err(_) => {
                        println!("Input processing timed out");
                        *state.lock().await = RunnerState::Error;
                    }
                }
            }
            println!("Input channel closed for container {}", input_container_id);
        });

        println!("I/O setup completed for container {}", self.container_id);
        Ok(())
    }
} 