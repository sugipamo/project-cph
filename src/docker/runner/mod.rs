pub mod command;

use std::sync::Arc;
use tokio::sync::Mutex;
use tokio::time::{timeout, Duration};

use crate::docker::state::RunnerState;
use crate::docker::config::DockerConfig;
use self::command::DockerCommand;

pub struct DockerRunner {
    command: DockerCommand,
    config: DockerConfig,
    language_info: LanguageInfo,
    state: Arc<Mutex<RunnerState>>,
}

impl DockerRunner {
    pub fn new(config: DockerConfig, language_info: LanguageInfo) -> Self {
        Self {
            command: DockerCommand::new(),
            config,
            language_info,
            state: Arc::new(Mutex::new(RunnerState::Ready)),
        }
    }

    pub fn from_language(language: &str) -> std::io::Result<Self> {
        let config = DockerConfig::default();
        let language_info = LanguageConfig::from_yaml("src/config/languages.yaml", language)?;
        
        Ok(Self::new(config, language_info))
    }

    pub async fn run_in_docker(&mut self, source_code: &str) -> Result<String, String> {
        println!("Starting Docker execution with image: {}", self.language_info.runner.image);
        
        match timeout(
            Duration::from_secs(self.config.timeout_seconds),
            self.execute(source_code)
        ).await {
            Ok(result) => result,
            Err(_) => {
                println!("Execution timed out after {} seconds", self.config.timeout_seconds);
                if let Err(e) = self.cleanup().await {
                    println!("Failed to cleanup after timeout: {}", e);
                }
                *self.state.lock().await = RunnerState::Error;
                Err("Execution timeout".to_string())
            }
        }
    }

    async fn execute(&mut self, source_code: &str) -> Result<String, String> {
        // 初期化
        self.initialize().await?;

        // コンパイルが必要な言語の場合
        if self.language_info.runner.needs_compilation() {
            println!("Compiling source code...");
            if let Some(ref compile_cmd) = self.language_info.runner.compile {
                if let Err(e) = self.command.compile(
                    &self.language_info.runner.image,
                    compile_cmd.as_slice(),
                    self.language_info.runner.get_compile_dir(),
                    &self.config.mount_point,
                    source_code,
                    self.language_info.runner.to_compile_config(&self.language_info.extension),
                ).await {
                    println!("Compilation failed: {}", e);
                    return Err(e);
                }
            }
        }

        // 実行
        let output = self.command.run_container(
            &self.language_info.runner.image,
            self.language_info.runner.run.as_slice(),
            source_code,
            self.config.timeout_seconds,
            self.config.memory_limit_mb,
            if self.language_info.runner.needs_compilation() {
                Some(self.language_info.runner.get_compile_dir())
            } else {
                None
            },
            &self.config.mount_point,
        ).await;

        // クリーンアップ
        if let Err(e) = self.cleanup().await {
            println!("Cleanup failed: {}", e);
        }

        output
    }

    async fn initialize(&mut self) -> Result<(), String> {
        println!("Initializing Docker runner");
        *self.state.lock().await = RunnerState::Running;

        // イメージの確認と取得
        if !self.command.check_image(&self.language_info.runner.image).await {
            println!("Image not found, attempting to pull: {}", self.language_info.runner.image);
            if !self.command.pull_image(&self.language_info.runner.image).await {
                println!("Failed to pull image: {}", self.language_info.runner.image);
                *self.state.lock().await = RunnerState::Error;
                return Err(format!("Failed to pull image: {}", self.language_info.runner.image));
            }
        }

        println!("Image is ready: {}", self.language_info.runner.image);
        *self.state.lock().await = RunnerState::Running;
        Ok(())
    }

    pub async fn cleanup(&mut self) -> Result<(), String> {
        println!("Cleaning up Docker runner");
        if self.command.stop_container().await {
            println!("Container stopped successfully");
            *self.state.lock().await = RunnerState::Stop;
            Ok(())
        } else {
            println!("Failed to stop container");
            *self.state.lock().await = RunnerState::Error;
            Err("Failed to stop container".to_string())
        }
    }

    pub async fn get_state(&self) -> RunnerState {
        self.state.lock().await.clone()
    }

    pub async fn inspect_mount_point(&mut self) -> Result<String, String> {
        println!("Inspecting mount point directory: {}", self.config.mount_point);
        self.command.inspect_directory(&self.language_info.runner.image, &self.config.mount_point).await
    }
} 