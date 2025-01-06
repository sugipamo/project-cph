use std::sync::Arc;
use tokio::sync::Mutex;
use thiserror::Error;
use crate::docker::state::RunnerState;
use crate::docker::traits::ContainerManager;
use crate::config::Config;

// New error type
#[derive(Error, Debug)]
pub enum CompilerError {
    #[error("言語の解決に失敗しました: {0}")]
    LanguageResolution(String),
    #[error("コンテナの作成に失敗しました: {0}")]
    ContainerCreation(String),
    #[error("コンテナの起動に失敗しました: {0}")]
    ContainerStartup(String),
    #[error("設定エラー: {0}")]
    Config(String),
}

// New trait for compilation operations
pub trait CompilationManager {
    async fn compile(&mut self, language: &str) -> Result<(), CompilerError>;
    async fn cleanup(&mut self) -> Result<(), CompilerError>;
}

pub(super) struct DockerCompiler {
    container_manager: Arc<Mutex<dyn ContainerManager>>,
    config: Arc<Config>,
    state: Arc<Mutex<RunnerState>>,
    stdout_buffer: Arc<Mutex<Vec<String>>>,
    stderr_buffer: Arc<Mutex<Vec<String>>>,
}

impl DockerCompiler {
    pub(super) fn new(
        container_manager: Arc<Mutex<dyn ContainerManager>>,
        config: Config,
        state: Arc<Mutex<RunnerState>>,
        stdout_buffer: Arc<Mutex<Vec<String>>>,
        stderr_buffer: Arc<Mutex<Vec<String>>>,
    ) -> Self {
        Self {
            container_manager,
            config: Arc::new(config),
            state,
            stdout_buffer,
            stderr_buffer,
        }
    }
}

impl CompilationManager for DockerCompiler {
    async fn compile(&mut self, language: &str) -> Result<(), CompilerError> {
        // 言語の設定を取得
        let lang_config = self.config.get_with_alias::<String>(&format!("{}.name", language))
            .map_err(|e| CompilerError::LanguageResolution(e.to_string()))?;

        // コンテナを作成
        let mut manager = self.container_manager.lock().await;
        manager.create_container(&lang_config, vec![], "/workspace")
            .await
            .map_err(|e| CompilerError::ContainerCreation(e.to_string()))?;

        // コンテナを起動
        manager.start_container()
            .await
            .map_err(|e| CompilerError::ContainerStartup(e.to_string()))?;

        Ok(())
    }

    async fn cleanup(&mut self) -> Result<(), CompilerError> {
        let mut manager = self.container_manager.lock().await;
        manager.stop_container()
            .await
            .map_err(|e| CompilerError::ContainerStartup(e.to_string()))?;
        Ok(())
    }
}