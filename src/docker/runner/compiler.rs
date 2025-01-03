use std::sync::Arc;
use tokio::sync::Mutex;
use bollard::Docker;
use bollard::container::{Config as DockerConfig, CreateContainerOptions, HostConfig};
use bollard::exec::{CreateExecOptions, StartExecOptions};
use crate::docker::state::RunnerState;
use crate::config::Config;

pub(super) struct DockerCompiler {
    docker: Docker,
    container_id: String,
    config: Arc<Config>,
    state: Arc<Mutex<RunnerState>>,
    stdout_buffer: Arc<Mutex<Vec<String>>>,
    stderr_buffer: Arc<Mutex<Vec<String>>>,
}

impl DockerCompiler {
    pub(super) fn new(
        docker: Docker,
        config: Config,
        state: Arc<Mutex<RunnerState>>,
        stdout_buffer: Arc<Mutex<Vec<String>>>,
        stderr_buffer: Arc<Mutex<Vec<String>>>,
    ) -> Self {
        Self {
            docker,
            container_id: String::new(),
            config: Arc::new(config),
            state,
            stdout_buffer,
            stderr_buffer,
        }
    }

    pub(super) async fn compile(&mut self, language: &str) -> Result<(), String> {
        // エイリアス解決を使用して言語名を取得
        let resolved_lang = self.config.get_with_alias::<String>(&format!("{}.name", language))
            .map_err(|e| format!("言語名の解決に失敗しました: {}", e))?;

        // 言語固有の設定を取得
        let image = self.config.get::<String>(&format!("languages.{}.runner.image", resolved_lang))
            .map_err(|e| format!("イメージ設定の取得に失敗しました: {}", e))?;
        let compile_cmd = self.config.get::<Vec<String>>(&format!("languages.{}.runner.compile", resolved_lang))
            .map_err(|e| format!("コンパイルコマンドの取得に失敗しました: {}", e))?;
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

        // コンテナの作成
        let container = match self.docker
            .create_container(
                Some(CreateContainerOptions {
                    name: "",
                    platform: None,
                }),
                DockerConfig {
                    image: Some(image.clone()),
                    cmd: Some(compile_cmd),
                    working_dir: Some(compile_dir.clone()),
                    tty: Some(false),
                    attach_stdin: Some(true),
                    attach_stdout: Some(true),
                    attach_stderr: Some(true),
                    open_stdin: Some(true),
                    host_config: Some(HostConfig {
                        auto_remove: Some(true),
                        memory: Some(self.config.get::<u64>("system.docker.memory_limit_mb")
                            .unwrap_or(256) * 1024 * 1024),
                        memory_swap: Some(0),
                        oom_kill_disable: Some(false),
                        nano_cpus: Some(1_000_000_000),
                        security_opt: Some(vec![
                            String::from("seccomp=unconfined"),
                        ]),
                        binds: Some(vec![
                            format!("{}:{}", self.config.get::<String>("system.docker.mount_point")
                                .unwrap_or_else(|_| "/compile".to_string()), compile_dir),
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

        // コンテナの起動
        println!("Starting container: {}", self.container_id);
        if let Err(e) = self.docker
            .start_container(&self.container_id, None::<StartContainerOptions<String>>)
            .await {
            println!("Failed to start container: {:?}", e);
            *self.state.lock().await = RunnerState::Error;
            return Err(format!("コンテナの起動に失敗しました: {}", e));
        }

        // コンパイル処理の実行
        println!("Running compilation for container: {}", self.container_id);
        let exec = match self.docker
            .create_exec(
                &self.container_id,
                CreateExecOptions {
                    attach_stdin: Some(true),
                    attach_stdout: Some(true),
                    attach_stderr: Some(true),
                    cmd: Some(compile_cmd),
                    ..Default::default()
                },
            )
            .await {
                Ok(exec) => exec,
                Err(e) => {
                    println!("Failed to create exec: {:?}", e);
                    *self.state.lock().await = RunnerState::Error;
                    return Err(format!("コンパイル実行の作成に失敗しました: {}", e));
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
                *self.state.lock().await = RunnerState::Error;
                return Err("コンパイル実行に失敗しました: 予期しない実行結果".to_string());
            }
            Err(e) => {
                println!("Failed to start exec: {:?}", e);
                *self.state.lock().await = RunnerState::Error;
                return Err(format!("コンパイル実行の開始に失敗しました: {}", e));
            }
        }

        // コンパイルエラーをチェック
        let stderr = self.read_error().await;
        if !stderr.is_empty() {
            println!("Compilation error: {}", stderr);
            *self.state.lock().await = RunnerState::Error;
            return Err(format!("コンパイルエラー: {}", stderr));
        }

        Ok(())
    }

    async fn read_error(&self) -> String {
        self.stderr_buffer.lock().await.join("\n")
    }
} 