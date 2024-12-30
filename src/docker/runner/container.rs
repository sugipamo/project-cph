use bollard::container::{Config, CreateContainerOptions, StartContainerOptions};
use bollard::models::HostConfig;
use bollard::image::CreateImageOptions;
use futures::StreamExt;
use std::time::Duration;

use crate::docker::error::{DockerError, Result};
use crate::docker::state::RunnerState;
use super::DockerRunner;

impl DockerRunner {
    pub async fn initialize(&mut self, source_code: &str) -> Result<()> {
        let current_state = self.state.lock().await.clone();
        println!("Initializing container with state: {:?}", current_state);
        if current_state != RunnerState::Ready {
            println!("Invalid state transition from {:?} to Running", current_state);
            return Err(DockerError::InvalidStateTransition {
                from: current_state.to_string(),
                to: RunnerState::Running.to_string(),
            });
        }

        let lang_config = self.config.get_language_config(&self.language)
            .ok_or_else(|| DockerError::UnsupportedLanguage(self.language.clone()))?
            .clone();

        // イメージの存在確認と取得
        println!("Checking for image: {}", lang_config.image);
        let mut pull_needed = true;
        if let Ok(images) = self.docker.list_images(None).await {
            if images.iter().any(|img| {
                img.repo_tags.as_ref()
                    .map_or(false, |tags| tags.contains(&lang_config.image))
            }) {
                pull_needed = false;
            }
        }

        if pull_needed {
            println!("Pulling image: {}", lang_config.image);
            let options = CreateImageOptions {
                from_image: lang_config.image.clone(),
                ..Default::default()
            };

            let mut pull_stream = self.docker.create_image(Some(options), None, None);
            while let Some(result) = pull_stream.next().await {
                if let Err(e) = result {
                    println!("Error pulling image: {:?}", e);
                    return Err(DockerError::RuntimeError(format!("Failed to pull image: {}", e)));
                }
            }
        }

        // コマンドの準備
        let mut cmd = lang_config.run.clone();
        cmd.push(source_code.to_string());
        println!("Command to run: {:?}", cmd);

        // コンテナの作成
        let container = match self.docker
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
                        "PYTHONIOENCODING=utf-8".to_string(),
                    ]),
                    ..Default::default()
                },
            )
            .await {
                Ok(container) => container,
                Err(e) => {
                    println!("Failed to create container: {:?}", e);
                    *self.state.lock().await = RunnerState::Error;
                    return Err(DockerError::ConnectionError(e));
                }
            };

        self.container_id = container.id.clone();
        println!("Container created with ID: {}", self.container_id);

        // コンパナの起動
        println!("Starting container: {}", self.container_id);
        if let Err(e) = self.docker
            .start_container(&self.container_id, None::<StartContainerOptions<String>>)
            .await {
            println!("Failed to start container: {:?}", e);
            *self.state.lock().await = RunnerState::Error;
            return Err(DockerError::ConnectionError(e));
        }

        // コンパイル処理の実行
        println!("Running compilation for container: {}", self.container_id);
        if let Err(e) = self.compile(lang_config).await {
            println!("Compilation failed: {:?}", e);
            *self.state.lock().await = RunnerState::Error;
            return Err(e);
        }

        // I/O設定
        println!("Setting up I/O for container: {}", self.container_id);
        if let Err(e) = self.setup_io().await {
            println!("Failed to setup I/O: {:?}", e);
            *self.state.lock().await = RunnerState::Error;
            return Err(e);
        }

        // 初期化完了を待機
        println!("Waiting for container initialization...");
        tokio::time::sleep(std::time::Duration::from_millis(500)).await;

        // 最終状態チェック
        match self.docker.inspect_container(&self.container_id, None).await {
            Ok(info) => {
                if let Some(state) = info.state {
                    if !state.running.unwrap_or(false) {
                        println!("Container is not running after initialization");
                        *self.state.lock().await = RunnerState::Error;
                        return Err(DockerError::RuntimeError("Container failed to start properly".to_string()));
                    }
                }
            }
            Err(e) => {
                println!("Failed to inspect container: {:?}", e);
                *self.state.lock().await = RunnerState::Error;
                return Err(DockerError::ConnectionError(e));
            }
        }

        println!("Container {} initialized successfully", self.container_id);
        *self.state.lock().await = RunnerState::Running;
        Ok(())
    }

    pub async fn stop(&mut self) -> Result<()> {
        let current_state = self.state.lock().await.clone();
        println!("Attempting to stop container {} (Current state: {:?})", self.container_id, current_state);

        // すでに停止している場合は早期リターン
        if current_state == RunnerState::Stop {
            return Ok(());
        }

        // まず通常の停止を試みる
        let stop_options = bollard::container::StopContainerOptions { t: 10 };
        match self.docker.stop_container(&self.container_id, Some(stop_options)).await {
            Ok(_) => {
                println!("Container {} stopped successfully", self.container_id);
                *self.state.lock().await = RunnerState::Stop;
                Ok(())
            }
            Err(e) => {
                println!("Failed to stop container gracefully: {}", e);
                if e.to_string().contains("No such container") {
                    println!("Container {} no longer exists", self.container_id);
                    *self.state.lock().await = RunnerState::Stop;
                    Ok(())
                } else {
                    // 強制停止を試みる
                    println!("Attempting force stop for container {}", self.container_id);
                    self.force_stop().await
                }
            }
        }
    }

    pub async fn check_state(&mut self) -> Result<RunnerState> {
        if self.container_id.is_empty() {
            return Ok(self.state.lock().await.clone());
        }

        match self.docker.inspect_container(&self.container_id, None).await {
            Ok(info) => {
                if let Some(state) = info.state {
                    let status = state.status.map(|s| s.to_string());
                    let running = state.running.unwrap_or(false);
                    let exit_code = state.exit_code.unwrap_or(-1);
                    let pid = state.pid.unwrap_or(0);

                    println!("Container {} state check - Status: {:?}, Running: {:?}, ExitCode: {:?}, Pid: {:?}",
                        self.container_id, status, running, exit_code, pid);

                    // 終了状態の判定を改善
                    let is_stopped = match (status.as_deref(), running, exit_code, pid) {
                        // 明示的な停止状態
                        (Some("exited" | "dead"), _, _, _) => true,
                        // 実行中でない
                        (_, false, _, _) => true,
                        // 終了コードが設定されている
                        (_, _, code, _) if code != 0 => true,
                        // プロセスIDが無効
                        (_, _, _, 0) => true,
                        _ => false
                    };

                    if is_stopped {
                        println!("Container {} has stopped", self.container_id);
                        *self.state.lock().await = RunnerState::Stop;
                        Ok(RunnerState::Stop)
                    } else {
                        Ok(RunnerState::Running)
                    }
                } else {
                    println!("Container {} state information not available", self.container_id);
                    Ok(RunnerState::Running)
                }
            }
            Err(e) => {
                println!("Failed to inspect container {}: {:?}", self.container_id, e);
                if e.to_string().contains("No such container") {
                    println!("Container {} no longer exists", self.container_id);
                    *self.state.lock().await = RunnerState::Stop;
                    Ok(RunnerState::Stop)
                } else {
                    Err(DockerError::InspectError(e.to_string()))
                }
            }
        }
    }

    pub async fn wait_for_stop(&mut self, timeout: Duration) -> Result<()> {
        let start = std::time::Instant::now();
        let check_interval = Duration::from_millis(50);

        while start.elapsed() < timeout {
            match self.check_state().await? {
                RunnerState::Stop => return Ok(()),
                RunnerState::Error => return Ok(()),
                _ => {
                    // コンテナの状態を直接確認
                    if let Ok(info) = self.docker.inspect_container(&self.container_id, None).await {
                        if let Some(state) = info.state {
                            let is_stopped = !state.running.unwrap_or(false) || 
                                           state.status.map(|s| s.to_string())
                                               .map(|s| s == "exited" || s == "dead")
                                               .unwrap_or(false);

                            if is_stopped {
                                println!("Container {} has stopped (direct check)", self.container_id);
                                *self.state.lock().await = RunnerState::Stop;
                                return Ok(());
                            }
                        }
                    }
                    tokio::time::sleep(check_interval).await;
                }
            }
        }

        // タイムアウト時は強制停止を試みる
        println!("Wait for stop timed out after {:?}, attempting force stop", timeout);
        self.force_stop().await?;
        Err(DockerError::Timeout)
    }

    pub async fn force_stop(&mut self) -> Result<()> {
        if self.container_id.is_empty() {
            return Ok(());
        }

        println!("Force stopping container {}", self.container_id);
        let kill_options = bollard::container::KillContainerOptions {
            signal: "SIGKILL",
        };

        match self.docker.kill_container(&self.container_id, Some(kill_options)).await {
            Ok(_) => {
                println!("Container {} killed successfully", self.container_id);
                *self.state.lock().await = RunnerState::Stop;
                Ok(())
            }
            Err(e) => {
                println!("Failed to kill container {}: {:?}", self.container_id, e);
                if e.to_string().contains("No such container") {
                    println!("Container {} no longer exists", self.container_id);
                    *self.state.lock().await = RunnerState::Stop;
                    Ok(())
                } else {
                    Err(DockerError::ConnectionError(e))
                }
            }
        }
    }
} 