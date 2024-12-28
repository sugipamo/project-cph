use async_trait::async_trait;
use bollard::container::{Config, CreateContainerOptions, StartContainerOptions};
use bollard::exec::{CreateExecOptions, StartExecResults};
use bollard::Docker;
use futures::StreamExt;
use std::sync::Arc;
use tokio::sync::Mutex;
use tokio::time::{Duration, timeout};
use std::path::Path;
use serde::Deserialize;

#[derive(Debug, Clone, PartialEq)]
pub enum RunnerState {
    Ready,
    Running,
    Stop,
    Error,
}

#[derive(Debug, Clone, Deserialize)]
pub struct LanguageConfig {
    pub image_name: String,
    pub compile_cmd: Option<Vec<String>>,
    pub run_cmd: Vec<String>,
    pub file_extension: String,
    pub workspace_dir: String,
}

#[derive(Debug, Clone, Deserialize)]
pub struct Languages {
    pub python: LanguageConfig,
    pub cpp: LanguageConfig,
    pub rust: LanguageConfig,
}

#[derive(Debug, Clone, Deserialize)]
pub struct RunnerConfig {
    pub timeout_seconds: u64,
    pub memory_limit_mb: i64,
    pub languages: Languages,
}

impl RunnerConfig {
    pub fn load<P: AsRef<Path>>(path: P) -> Result<Self, Box<dyn std::error::Error>> {
        let config_str = std::fs::read_to_string(path)?;
        let config: RunnerConfig = serde_yaml::from_str(&config_str)?;
        Ok(config)
    }

    pub fn get_language_config(&self, lang: &str) -> Option<&LanguageConfig> {
        match lang {
            "python" => Some(&self.languages.python),
            "cpp" => Some(&self.languages.cpp),
            "rust" => Some(&self.languages.rust),
            _ => None,
        }
    }
}

pub struct DockerRunner {
    docker: Docker,
    container_id: String,
    state: Arc<Mutex<RunnerState>>,
    stdout_buffer: Arc<Mutex<Vec<String>>>,
    stderr_buffer: Arc<Mutex<Vec<String>>>,
    stdin_tx: Option<tokio::sync::mpsc::Sender<String>>,
    config: RunnerConfig,
    language: String,
}

impl DockerRunner {
    pub async fn new<P: AsRef<Path>>(config_path: P, language: &str) -> Result<Self, Box<dyn std::error::Error>> {
        let config = RunnerConfig::load(config_path)?;
        
        if config.get_language_config(language).is_none() {
            return Err(format!("Unsupported language: {}", language).into());
        }

        let docker = Docker::connect_with_local_defaults()?;
        let state = Arc::new(Mutex::new(RunnerState::Ready));
        let stdout_buffer = Arc::new(Mutex::new(Vec::new()));
        let stderr_buffer = Arc::new(Mutex::new(Vec::new()));

        Ok(Self {
            docker,
            container_id: String::new(),
            state,
            stdout_buffer,
            stderr_buffer,
            stdin_tx: None,
            config,
            language: language.to_string(),
        })
    }

    pub async fn initialize(&mut self, source_code: &str) -> Result<(), Box<dyn std::error::Error>> {
        let lang_config = self.config.get_language_config(&self.language)
            .ok_or_else(|| format!("Language not found: {}", self.language))?;

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
            result?;
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
            .await?;

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
                .await?;

            match self.docker.start_exec(&exec.id, None).await? {
                StartExecResults::Attached { mut output, .. } => {
                    while let Some(Ok(output)) = output.next().await {
                        match output {
                            OutputType::StdErr(bytes) => {
                                let mut stderr = self.stderr_buffer.lock().await;
                                stderr.push(String::from_utf8_lossy(&bytes).to_string());
                            }
                            _ => {}
                        }
                    }
                }
                _ => return Err("Compilation failed".into()),
            }

            // コンパイルエラーをチェック
            let stderr = self.read_error().await?;
            if !stderr.is_empty() {
                *self.state.lock().await = RunnerState::Error;
                return Err("Compilation error".into());
            }
        }

        // 入力チャネルの設定
        let (tx, mut rx) = tokio::sync::mpsc::channel::<String>(32);
        self.stdin_tx = Some(tx);

        // コンテナの起動とI/O処理の開始
        self.docker
            .start_container(&self.container_id, None::<StartContainerOptions<String>>)
            .await?;

        let container_id = self.container_id.clone();
        let docker = self.docker.clone();
        let stdout_buffer = self.stdout_buffer.clone();
        let stderr_buffer = self.stderr_buffer.clone();
        let state = self.state.clone();
        let timeout_duration = Duration::from_secs(self.config.timeout_seconds);

        // 入力処理用のタスク
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
                    Ok(Ok(StartExecResults::Attached { mut output, .. })) => {
                        while let Some(Ok(output)) = output.next().await {
                            match output {
                                OutputType::StdOut(bytes) => {
                                    let mut stdout = stdout_buffer.lock().await;
                                    stdout.push(String::from_utf8_lossy(&bytes).to_string());
                                }
                                OutputType::StdErr(bytes) => {
                                    let mut stderr = stderr_buffer.lock().await;
                                    stderr.push(String::from_utf8_lossy(&bytes).to_string());
                                }
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

        *self.state.lock().await = RunnerState::Running;
        Ok(())
    }

    // ... 他のメソッドは変更なし ...
}

impl Drop for DockerRunner {
    fn drop(&mut self) {
        if !self.container_id.is_empty() {
            let docker = self.docker.clone();
            let container_id = self.container_id.clone();
            tokio::spawn(async move {
                let _ = docker.remove_container(&container_id, None).await;
            });
        }
    }
} 