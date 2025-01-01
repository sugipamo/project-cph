pub mod command;

use std::sync::Arc;
use tokio::sync::Mutex;
use tokio::time::{timeout, Duration};

use crate::docker::state::RunnerState;
use crate::docker::config::DockerConfig;
use crate::config::Config;
use self::command::DockerCommand;

pub struct DockerRunner {
    command: DockerCommand,
    config: DockerConfig,
    state: Arc<Mutex<RunnerState>>,
}

impl DockerRunner {
    pub fn new(config: DockerConfig) -> Self {
        Self {
            command: DockerCommand::new(),
            config,
            state: Arc::new(Mutex::new(RunnerState::Ready)),
        }
    }

    pub fn from_language(language: &str) -> std::io::Result<Self> {
        let config = DockerConfig::default();
        let config_builder = Config::builder()
            .map_err(|e| std::io::Error::new(std::io::ErrorKind::Other, e.to_string()))?;

        // エイリアス解決を使用して言語名を取得
        let resolved = config_builder.get_with_alias::<String>(&format!("{}.name", language))
            .map_err(|e| std::io::Error::new(std::io::ErrorKind::Other, e.to_string()))?;

        // 言語設定を取得
        let runner_image = config_builder.get::<String>(&format!("{}.runner.image", resolved))
            .map_err(|e| std::io::Error::new(std::io::ErrorKind::Other, e.to_string()))?;

        let compile_command = config_builder.get::<Vec<String>>(&format!("{}.runner.compile", resolved))
            .unwrap_or_default();

        let run_command = config_builder.get::<Vec<String>>(&format!("{}.runner.run", resolved))
            .map_err(|e| std::io::Error::new(std::io::ErrorKind::Other, e.to_string()))?;

        let needs_compilation = config_builder.get::<bool>(&format!("{}.runner.needs_compilation", resolved))
            .unwrap_or(false);

        let compile_dir = config_builder.get::<String>(&format!("{}.runner.compile_dir", resolved))
            .unwrap_or_else(|_| "/workspace".to_string());

        let extension = config_builder.get::<String>(&format!("{}.extension", resolved))
            .map_err(|e| std::io::Error::new(std::io::ErrorKind::Other, e.to_string()))?;

        Ok(Self::new(config))
    }

    pub async fn run_in_docker(&mut self, source_code: &str) -> Result<String, String> {
        println!("Starting Docker execution");
        
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

        // 設定を取得
        let config_builder = Config::builder()
            .map_err(|e| format!("設定の読み込みに失敗しました: {}", e))?;

        // 言語設定を取得
        let needs_compilation = config_builder.get::<bool>("runner.needs_compilation")
            .unwrap_or(false);

        // コンパイルが必要な言語の場合
        if needs_compilation {
            println!("Compiling source code...");
            let compile_cmd = config_builder.get::<Vec<String>>("runner.compile")
                .unwrap_or_default();

            if !compile_cmd.is_empty() {
                if let Err(e) = self.command.compile(
                    &config_builder.get::<String>("runner.image")?,
                    &compile_cmd,
                    &config_builder.get::<String>("runner.compile_dir")?,
                    &self.config.mount_point,
                    source_code,
                    config_builder.get::<String>("extension")?,
                ).await {
                    println!("Compilation failed: {}", e);
                    return Err(e);
                }
            }
        }

        // 実行
        let output = self.command.run_container(
            &config_builder.get::<String>("runner.image")?,
            &config_builder.get::<Vec<String>>("runner.run")?,
            source_code,
            self.config.timeout_seconds,
            self.config.memory_limit_mb,
            if needs_compilation {
                Some(config_builder.get::<String>("runner.compile_dir")?)
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

        // 設定を取得
        let config_builder = Config::builder()
            .map_err(|e| format!("設定の読み込みに失敗しました: {}", e))?;

        // イメージ名を取得
        let image = config_builder.get::<String>("runner.image")
            .map_err(|e| format!("イメージ名の取得に失敗しました: {}", e))?;

        // イメージの確認と取得
        if !self.command.check_image(&image).await {
            println!("Image not found, attempting to pull: {}", image);
            if !self.command.pull_image(&image).await {
                println!("Failed to pull image: {}", image);
                *self.state.lock().await = RunnerState::Error;
                return Err(format!("Failed to pull image: {}", image));
            }
        }

        println!("Image is ready: {}", image);
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
        // 設定を取得
        let config_builder = Config::builder()
            .map_err(|e| format!("設定の読み込みに失敗しました: {}", e))?;

        // イメージ名を取得
        let image = config_builder.get::<String>("runner.image")
            .map_err(|e| format!("イメージ名の取得に失敗しました: {}", e))?;

        println!("Inspecting mount point directory: {}", self.config.mount_point);
        self.command.inspect_directory(&image, &self.config.mount_point).await
    }
} 