pub mod command;

use std::sync::Arc;
use tokio::sync::Mutex;
use std::path::PathBuf;
use std::process::Stdio;
use tokio::process::Command;

use crate::config::Config;
use crate::config::TypedValue;
use self::command::DockerCommand;
use crate::docker::state::RunnerState;

pub struct DockerRunner {
    command: DockerCommand,
    config: Arc<Config>,
    language: String,
    state: Arc<Mutex<RunnerState>>,
}

impl DockerRunner {
    fn load_config_value<T: TypedValue>(config: &Config, key: &str) -> Result<T, String> {
        config.get::<T>(key)
            .map_err(|e| format!("設定の読み込みに失敗しました: {}", e))
    }

    pub fn new(config: Config, language: String) -> Result<Self, String> {
        // 言語の存在確認
        let config = Arc::new(config);
        let _resolved = config.get_with_alias::<String>(&format!("languages.{}.extension", language))
            .map_err(|e| format!("言語名の解決に失敗しました: {}", e))?;

        Ok(Self {
            command: DockerCommand::new(),
            config: config.clone(),
            language,
            state: Arc::new(Mutex::new(RunnerState::Ready)),
        })
    }

    pub fn from_language(language: &str) -> Result<Self, String> {
        let config = Config::load()
            .map_err(|e| format!("設定の読み込みに失敗しました: {}", e))?;
        
        Self::new(config, language.to_string())
    }

    pub async fn run_in_docker(&mut self, source_code: &str) -> Result<String, String> {
        println!("Starting Docker execution");
        
        // イメージ名を取得
        let image = self.config.get::<String>(&format!("languages.{}.runner.image", self.language))
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

        // ソースコードの実行
        let result = self.command.run_code(&image, source_code).await;
        match result {
            Ok(output) => {
                *self.state.lock().await = RunnerState::Ready;
                Ok(output)
            }
            Err(e) => {
                *self.state.lock().await = RunnerState::Error;
                Err(e)
            }
        }
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
        // イメージ名を取得
        let image = self.config.get::<String>(&format!("languages.{}.runner.image", self.language))
            .map_err(|e| format!("イメージ名の取得に失敗しました: {}", e))?;

        // マウントポイントを取得
        let mount_point = self.config.get::<String>("system.docker.mount_point")
            .map_err(|e| format!("マウントポイントの設定の読み込みに失敗しました: {}", e))?;

        println!("Inspecting mount point directory: {}", &mount_point);
        self.command.inspect_directory(&image, &mount_point).await
    }
} 