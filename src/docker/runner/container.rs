use bollard::container::{Config, CreateContainerOptions, StartContainerOptions};
use bollard::models::HostConfig;
use bollard::image::CreateImageOptions;
use futures::StreamExt;
use std::time::Duration;

use crate::docker::state::RunnerState;
use super::DockerRunner;

impl DockerRunner {
    pub async fn initialize(&mut self, source_code: &str) -> Result<(), String> {
        let current_state = self.state.lock().await.clone();
        println!("Initializing container with state: {:?}", current_state);
        if current_state != RunnerState::Ready {
            println!("Invalid state transition from {:?} to Running", current_state);
            return Err(format!("不正な状態遷移です: {:?} -> Running", current_state));
        }

        // エイリアス解決を使用して言語名を取得
        let resolved_lang = self.config.get_with_alias::<String>(&format!("{}.name", self.language))
            .map_err(|e| format!("言語名の解決に失敗しました: {}", e))?;

        // 言語固有の設定を取得
        let image = self.config.get::<String>(&format!("languages.{}.runner.image", resolved_lang))
            .map_err(|e| format!("イメージ設定の取得に失敗しました: {}", e))?;
        let run_cmd = self.config.get::<Vec<String>>(&format!("languages.{}.runner.run", resolved_lang))
            .map_err(|e| format!("実行コマンドの取得に失敗しました: {}", e))?;
        let compile_dir = self.config.get::<String>(&format!("languages.{}.runner.compile_dir", resolved_lang))
            .map_err(|e| format!("コンパイルディレクトリの取得に失敗しました: {}", e))?;
        let env_vars = self.config.get::<Vec<String>>(&format!("languages.{}.runner.env_vars", resolved_lang))
            .unwrap_or_default();

        // イメージの存在確認と取得
        println!("Checking for image: {}", image);
        let mut pull_needed = true;
        if let Ok(images) = self.docker.list_images(None).await {
            if images.iter().any(|img| {
                img.repo_tags.as_ref()
                    .map(|tags| tags.contains(&image))
                    .unwrap_or(false)
            }) {
                pull_needed = false;
            }
        }

        if pull_needed {
            println!("Pulling image: {}", image);
            let options = CreateImageOptions {
                from_image: image.clone(),
                ..Default::default()
            };

            let mut pull_stream = self.docker.create_image(Some(options), None, None);
            while let Some(result) = pull_stream.next().await {
                if let Err(e) = result {
                    println!("Error pulling image: {:?}", e);
                    return Err(format!("イメージの取得に失敗しました: {}", e));
                }
            }
        }

        // コマンドの準備
        let mut cmd = run_cmd.clone();
        cmd.push(source_code.to_string());
        println!("Command to run: {:?}", cmd);

        // メモリ制限の取得
        let memory_limit = self.config.get::<u64>("system.docker.memory_limit_mb")
            .map_err(|e| format!("メモリ制限設定の取得に失敗しました: {}", e))?;

        // マウントポイントの取得
        let mount_point = self.config.get::<String>("system.docker.mount_point")
            .map_err(|e| format!("マウントポイント設定の取得に失敗しました: {}", e))?;

        // コンテナの作成
        let container = match self.docker
            .create_container(
                Some(CreateContainerOptions {
                    name: "",
                    platform: None,
                }),
                Config {
                    image: Some(image.clone()),
                    cmd: Some(cmd),
                    working_dir: Some(compile_dir.clone()),
                    tty: Some(false),
                    attach_stdin: Some(true),
                    attach_stdout: Some(true),
                    attach_stderr: Some(true),
                    open_stdin: Some(true),
                    host_config: Some(HostConfig {
                        auto_remove: Some(true),
                        memory: Some(memory_limit * 1024 * 1024),
                        memory_swap: Some(0),
                        oom_kill_disable: Some(false),
                        nano_cpus: Some(1_000_000_000),
                        security_opt: Some(vec![
                            String::from("seccomp=unconfined"),
                        ]),
                        binds: Some(vec![
                            format!("{}:{}", mount_point, compile_dir),
                        ]),
                        ..Default::default()
                    }),
                    env: Some(env_vars),
                    ..Default::default()
                },
            )
            .await {
                Ok(container) => container,
                Err(e) => {
                    println!("Failed to create container: {:?}", e);
                    *self.state.lock().await = RunnerState::Error;
                    return Err(format!("コンテナの作成に失敗しました: {}", e));
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
            return Err(format!("コンテナの起動に失敗しました: {}", e));
        }

        // I/O設定
        println!("Setting up I/O for container: {}", self.container_id);
        self.setup_io().await?;

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
                        return Err("初期化後にコンテナが実行状態ではありません".to_string());
                    }
                }
            }
            Err(e) => {
                println!("Failed to inspect container: {:?}", e);
                *self.state.lock().await = RunnerState::Error;
                return Err(format!("コンテナの状態確認に失敗しました: {}", e));
            }
        }

        println!("Container {} initialized successfully", self.container_id);
        *self.state.lock().await = RunnerState::Running;
        Ok(())
    }

    pub async fn stop(&mut self) -> () {
        let current_state = self.state.lock().await.clone();
        println!("Attempting to stop container {} (Current state: {:?})", self.container_id, current_state);

        if current_state == RunnerState::Stop {
            return;
        }

        let stop_options = bollard::container::StopContainerOptions { t: 10 };
        match self.docker.stop_container(&self.container_id, Some(stop_options)).await {
            Ok(_) => {
                println!("Container {} stopped successfully", self.container_id);
                *self.state.lock().await = RunnerState::Stop;
            }
            Err(e) => {
                println!("Failed to stop container gracefully: {}", e);
                if e.to_string().contains("No such container") {
                    println!("Container {} no longer exists", self.container_id);
                    *self.state.lock().await = RunnerState::Stop;
                } else {
                    println!("Attempting force stop for container {}", self.container_id);
                    self.force_stop().await;
                }
            }
        }
    }

    pub async fn check_state(&mut self) -> RunnerState {
        if self.container_id.is_empty() {
            return self.state.lock().await.clone();
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

                    let is_stopped = match (status.as_deref(), running, exit_code, pid) {
                        (Some("exited" | "dead"), _, _, _) => true,
                        (_, false, _, _) => true,
                        (_, _, code, _) if code != 0 => true,
                        (_, _, _, 0) => true,
                        _ => false
                    };

                    if is_stopped {
                        println!("Container {} has stopped", self.container_id);
                        *self.state.lock().await = RunnerState::Stop;
                        RunnerState::Stop
                    } else {
                        RunnerState::Running
                    }
                } else {
                    println!("Container {} state information not available", self.container_id);
                    RunnerState::Running
                }
            }
            Err(e) => {
                println!("Failed to inspect container {}: {:?}", self.container_id, e);
                if e.to_string().contains("No such container") {
                    println!("Container {} no longer exists", self.container_id);
                    *self.state.lock().await = RunnerState::Stop;
                    RunnerState::Stop
                } else {
                    println!("Error inspecting container: {}", e);
                    RunnerState::Error
                }
            }
        }
    }

    pub async fn wait_for_stop(&mut self, timeout: Duration) -> () {
        let start = std::time::Instant::now();
        let check_interval = Duration::from_millis(50);

        while start.elapsed() < timeout {
            match self.check_state().await {
                RunnerState::Stop | RunnerState::Error => return,
                _ => {
                    if let Ok(info) = self.docker.inspect_container(&self.container_id, None).await {
                        if let Some(state) = info.state {
                            let is_stopped = !state.running.unwrap_or(false) || 
                                           state.status.map(|s| s.to_string())
                                               .map(|s| s == "exited" || s == "dead")
                                               .unwrap_or(false);

                            if is_stopped {
                                println!("Container {} has stopped (direct check)", self.container_id);
                                *self.state.lock().await = RunnerState::Stop;
                                return;
                            }
                        }
                    }
                    tokio::time::sleep(check_interval).await;
                }
            }
        }

        println!("Wait for stop timed out after {:?}, attempting force stop", timeout);
        self.force_stop().await;
    }

    pub async fn force_stop(&mut self) -> () {
        if self.container_id.is_empty() {
            return;
        }

        println!("Force stopping container {}", self.container_id);
        let kill_options = bollard::container::KillContainerOptions {
            signal: "SIGKILL",
        };

        match self.docker.kill_container(&self.container_id, Some(kill_options)).await {
            Ok(_) => {
                println!("Container {} killed successfully", self.container_id);
                *self.state.lock().await = RunnerState::Stop;
            }
            Err(e) => {
                println!("Failed to kill container {}: {:?}", self.container_id, e);
                if e.to_string().contains("No such container") {
                    println!("Container {} no longer exists", self.container_id);
                    *self.state.lock().await = RunnerState::Stop;
                }
            }
        }
    }
} 