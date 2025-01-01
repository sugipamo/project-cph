pub mod command;

use std::sync::Arc;
use tokio::sync::Mutex;
use tokio::time::{timeout, Duration};

use crate::docker::state::RunnerState;
use crate::docker::config::DockerConfig;
use crate::config::Config;
use crate::config::ConfigError;
use self::command::{DockerCommand, CompileConfig};

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

    pub fn from_language(language: &str) -> Result<Self, ConfigError> {
        let config = DockerConfig::default()?;
        let config_builder = Config::builder()?;

        // エイリアス解決を使用して言語名を取得
        let resolved = config_builder.get_with_alias::<String>(&format!("{}.name", language))
            .map_err(|e| match e {
                ConfigError::PathError(_) => ConfigError::RequiredValueError(
                    format!("言語 '{}' の設定が見つかりません", language)
                ),
                _ => e
            })?;

        // 言語設定を取得
        let _runner_image = config_builder.get::<String>(&format!("{}.runner.image", resolved))
            .map_err(|e| match e {
                ConfigError::PathError(_) => ConfigError::RequiredValueError(
                    format!("言語 '{}' のイメージ設定が見つかりません", resolved)
                ),
                _ => e
            })?;

        let _compile_command = config_builder.get::<Vec<String>>(&format!("{}.runner.compile", resolved))
            .map_err(|e| match e {
                ConfigError::PathError(_) => ConfigError::RequiredValueError(
                    format!("言語 '{}' のコンパイルコマンド設定が見つかりません", resolved)
                ),
                _ => e
            })?;

        let _run_command = config_builder.get::<Vec<String>>(&format!("{}.runner.run", resolved))
            .map_err(|e| match e {
                ConfigError::PathError(_) => ConfigError::RequiredValueError(
                    format!("言語 '{}' の実行コマンド設定が見つかりません", resolved)
                ),
                _ => e
            })?;

        let _needs_compilation = config_builder.get::<bool>(&format!("{}.runner.needs_compilation", resolved))
            .map_err(|e| match e {
                ConfigError::PathError(_) => ConfigError::RequiredValueError(
                    format!("言語 '{}' のコンパイル要否設定が見つかりません", resolved)
                ),
                _ => e
            })?;

        let _extension = config_builder.get::<String>(&format!("{}.extension", resolved))
            .map_err(|e| match e {
                ConfigError::PathError(_) => ConfigError::RequiredValueError(
                    format!("言語 '{}' の拡張子設定が見つかりません", resolved)
                ),
                _ => e
            })?;

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
            .map_err(|e| format!("コンパイル設定の取得に失敗しました: {}", e))?;

        // コンパイルが必要な言語の場合
        if needs_compilation {
            println!("Compiling source code...");
            let compile_cmd = config_builder.get::<Vec<String>>("runner.compile")
                .map_err(|e| format!("コンパイルコマンドの取得に失敗しました: {}", e))?;

            if !compile_cmd.is_empty() {
                let image = config_builder.get::<String>("runner.image")
                    .map_err(|e| format!("イメージ名の取得に失敗しました: {}", e))?;
                let compile_dir = config_builder.get::<String>("runner.compile_dir")
                    .map_err(|e| format!("コンパイルディレクトリの取得に失敗しました: {}", e))?;

                let compile_config = CompileConfig::from_config(&config_builder, "runner")?;

                if let Err(e) = self.command.compile(
                    &image,
                    &compile_cmd,
                    &compile_dir,
                    &self.config.mount_point,
                    source_code,
                    compile_config,
                ).await {
                    println!("Compilation failed: {}", e);
                    return Err(e);
                }
            }
        }

        // 実行
        let image = config_builder.get::<String>("runner.image")
            .map_err(|e| format!("イメージ名の取得に失敗しました: {}", e))?;
        let run_cmd = config_builder.get::<Vec<String>>("runner.run")
            .map_err(|e| format!("実行コマンドの取得に失敗しました: {}", e))?;
        let compile_dir = if needs_compilation {
            Some(config_builder.get::<String>("runner.compile_dir")
                .map_err(|e| format!("コンパイルディレクトリの取得に失敗しました: {}", e))?)
        } else {
            None
        };

        let output = self.command.run_container(
            &image,
            &run_cmd,
            source_code,
            self.config.timeout_seconds,
            self.config.memory_limit_mb,
            compile_dir.as_deref(),
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