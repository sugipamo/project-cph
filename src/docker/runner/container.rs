use bollard::container::{Config, CreateContainerOptions, StartContainerOptions};
use bollard::models::{HostConfig, ResourcesUlimits};
use bollard::exec::{CreateExecOptions, StartExecResults};
use bollard::image::CreateImageOptions;
use futures::StreamExt;

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
                from_image: lang_config.image_name.clone(),
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
                Some(CreateContainerOptions {
                    name: "",
                    platform: None,
                }),
                Config {
                    image: Some(lang_config.image_name.clone()),
                    cmd: Some(cmd),
                    working_dir: Some(lang_config.workspace_dir.clone()),
                    tty: Some(true),
                    attach_stdin: Some(true),
                    attach_stdout: Some(true),
                    attach_stderr: Some(true),
                    open_stdin: Some(true),
                    host_config: Some(HostConfig {
                        memory: Some(self.config.memory_limit_mb * 1024 * 1024),  // メモリ制限（バイト単位）
                        memory_swap: Some(self.config.memory_limit_mb * 1024 * 1024),  // スワップ含めた制限
                        cpu_period: Some(100_000),  // デフォルトのCPU期間（マイクロ秒）
                        cpu_quota: Some(100_000),   // CPU使用量を100%に制限
                        security_opt: Some(vec![
                            String::from("seccomp=unconfined"),  // seccompフィルターを無効化
                        ]),
                        ulimits: Some(vec![
                            ResourcesUlimits {
                                name: Some(String::from("cpu")),
                                soft: Some(self.config.timeout_seconds as i64),
                                hard: Some(self.config.timeout_seconds as i64),
                            },
                            ResourcesUlimits {
                                name: Some(String::from("as")),  // アドレス空間の制限
                                soft: Some((self.config.memory_limit_mb * 1024 * 1024) as i64),
                                hard: Some((self.config.memory_limit_mb * 1024 * 1024) as i64),
                            },
                        ]),
                        ..Default::default()
                    }),
                    ..Default::default()
                },
            )
            .await
            .map_err(DockerError::ConnectionError)?;

        self.container_id = container.id.clone();

        // コンパイルが必要な場合は実行
        if let Some(compile_cmd) = &lang_config.compile_cmd {
            let exec = self.docker
                .create_exec(
                    &self.container_id,
                    CreateExecOptions {
                        cmd: Some(compile_cmd.clone()),
                        working_dir: Some(lang_config.workspace_dir.clone()),
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

            // コンテナの削除を追加
            self.docker
                .remove_container(
                    &self.container_id,
                    Some(bollard::container::RemoveContainerOptions {
                        force: true,
                        ..Default::default()
                    }),
                )
                .await
                .map_err(DockerError::ConnectionError)?;
        }

        *self.state.lock().await = RunnerState::Stop;
        Ok(())
    }
} 