use bollard::container::{Config, CreateContainerOptions, StartContainerOptions};
use bollard::models::HostConfig;
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
            .ok_or_else(|| DockerError::UnsupportedLanguage(self.language.clone()))?
            .clone();

        // イメージのプル
        let mut image_stream = self.docker.create_image(
            Some(CreateImageOptions {
                from_image: lang_config.image.clone(),
                ..Default::default()
            }),
            None,
            None,
        );

        while let Some(result) = image_stream.next().await {
            result.map_err(DockerError::ConnectionError)?;
        }

        // コンテナの作成
        let mut cmd = lang_config.run.clone();
        cmd.push(source_code.to_string());

        let container = self.docker
            .create_container(
                Some(CreateContainerOptions {
                    name: "",
                    platform: None,
                }),
                Config {
                    image: Some(lang_config.image.clone()),
                    cmd: Some(cmd),
                    working_dir: Some(lang_config.compile_dir.clone()),
                    tty: Some(false),
                    attach_stdin: Some(true),
                    attach_stdout: Some(true),
                    attach_stderr: Some(true),
                    open_stdin: Some(true),
                    host_config: Some(HostConfig {
                        auto_remove: Some(true),
                        memory: Some(self.config.memory_limit_mb * 1024 * 1024),
                        memory_swap: Some(self.config.memory_limit_mb * 1024 * 1024),
                        nano_cpus: Some(1_000_000_000),
                        security_opt: Some(vec![
                            String::from("seccomp=unconfined"),
                        ]),
                        binds: Some(vec![
                            format!("{}:{}", self.config.mount_point, lang_config.compile_dir),
                        ]),
                        ..Default::default()
                    }),
                    env: Some(vec![
                        "PYTHONUNBUFFERED=1".to_string(),
                    ]),
                    ..Default::default()
                },
            )
            .await
            .map_err(DockerError::ConnectionError)?;

        self.container_id = container.id.clone();

        // コンパナの起動
        self.docker
            .start_container(&self.container_id, None::<StartContainerOptions<String>>)
            .await
            .map_err(DockerError::ConnectionError)?;

        // コンパイル処理の実行（所有権を持つ設定を渡す）
        self.compile(lang_config).await?;

        // I/O設定
        self.setup_io().await?;

        *self.state.lock().await = RunnerState::Running;
        Ok(())
    }

    pub async fn stop(&mut self) -> Result<()> {
        let current_state = self.state.lock().await.clone();
        current_state.can_transition_to(&RunnerState::Stop)?;

        if !self.container_id.is_empty() {
            // まず通常の停止を試みる（10秒のタイムアウト）
            let stop_options = bollard::container::StopContainerOptions {
                t: 10,
            };

            match self.docker.stop_container(&self.container_id, Some(stop_options)).await {
                Ok(_) => (),
                Err(e) => {
                    println!("Warning: Failed to stop runner {}: {:?}", self.container_id, e);
                    // コンテナが存在しない場合は無視
                    if !e.to_string().contains("No such container") {
                        // 強制停止を試みる
                        let kill_options = bollard::container::KillContainerOptions {
                            signal: "SIGKILL",
                        };
                        match self.docker.kill_container(&self.container_id, Some(kill_options)).await {
                            Ok(_) => (),
                            Err(e) => {
                                if !e.to_string().contains("No such container") {
                                    return Err(DockerError::ConnectionError(e));
                                }
                            }
                        }
                    }
                }
            }
        }

        *self.state.lock().await = RunnerState::Stop;
        Ok(())
    }
} 