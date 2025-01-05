pub mod command;

use std::sync::Arc;
use tokio::sync::Mutex;
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

    pub async fn run(&mut self, source_code: &str) -> Result<DockerOutput, String> {
        // イメージ名を取得
        let image = self.config.get::<String>(&format!("languages.{}.runner.image", self.language))
            .map_err(|e| format!("イメージ名の取得に失敗しました: {}", e))?;

        // ソースコードの実行
        let result = self.command.run_code(&image, source_code).await;
        match result {
            Ok(output) => {
                *self.state.lock().await = RunnerState::Ready;
                Ok(output)
            }
            Err(e) => {
                *self.state.lock().await = RunnerState::Error;
                Err(format!("実行エラー: {}", e))
            }
        }
    }

    pub async fn cleanup(&mut self) -> Result<(), String> {
        let state = self.state.lock().await;
        if *state == RunnerState::Stop {
            return Ok(());
        }
        drop(state);

        if self.command.stop_container().await {
            *self.state.lock().await = RunnerState::Stop;
            Ok(())
        } else {
            *self.state.lock().await = RunnerState::Error;
            Err("コンテナの停止に失敗しました".to_string())
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

        self.command.inspect_directory(&image, &mount_point).await
            .map_err(|e| format!("マウントポイントの検査に失敗しました: {}", e))
    }
} 