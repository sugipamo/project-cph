use std::sync::Arc;
use std::time::Duration;
use crate::config::Config;
use crate::docker::runner::{DockerRunner, DockerCommandLayer, DefaultDockerExecutor, ContainerConfig};
use crate::docker::traits::DockerRunner as DockerRunnerTrait;
use crate::contest::error::{ContestResult, ContestError};

pub struct ContestService {
    config: Config,
}

impl ContestService {
    pub fn new(config: Config) -> Self {
        Self { config }
    }

    pub async fn run_code(&self, source_code: &str) -> ContestResult<String> {
        // 設定から必要な情報を取得
        let memory_limit = self.config.get::<u64>("system.docker.memory_limit_mb")
            .map_err(|e| ContestError::Config(format!("メモリ制限の取得に失敗: {}", e)))?;
        
        let mount_point = self.config.get::<String>("system.docker.mount_point")
            .map_err(|e| ContestError::Config(format!("マウントポイントの取得に失敗: {}", e)))?;
        
        let working_dir = self.config.get::<String>("system.docker.working_dir")
            .map_err(|e| ContestError::Config(format!("作業ディレクトリの取得に失敗: {}", e)))?;
        
        let image = self.config.get::<String>("system.docker.image")
            .map_err(|e| ContestError::Config(format!("Dockerイメージの取得に失敗: {}", e)))?;

        let timeout = self.config.get::<u64>("system.docker.timeout_seconds")
            .map_err(|e| ContestError::Config(format!("タイムアウト設定の取得に失敗: {}", e)))?;

        let run_cmd = self.config.get::<Vec<String>>("system.docker.run_cmd")
            .map_err(|e| ContestError::Config(format!("実行コマンドの取得に失敗: {}", e)))?;

        // DockerRunnerの設定
        let docker = Arc::new(DockerCommandLayer::new(Box::new(DefaultDockerExecutor::new())));
        let container_config = ContainerConfig {
            image,
            memory_limit,
            mount_point,
            working_dir,
        };

        let mut docker_runner = DockerRunner::new(
            docker,
            container_config,
            Duration::from_secs(timeout),
        );

        // コンテナの初期化と実行
        DockerRunnerTrait::initialize(&mut docker_runner, run_cmd).await
            .map_err(|e| ContestError::Docker(format!("コンテナの初期化に失敗: {}", e)))?;

        // ソースコードの書き込み
        DockerRunnerTrait::write(&mut docker_runner, source_code).await
            .map_err(|e| ContestError::Docker(format!("ソースコードの書き込みに失敗: {}", e)))?;

        // 実行結果の取得
        let output = DockerRunnerTrait::read_stdout(&mut docker_runner).await
            .map_err(|e| ContestError::Docker(format!("実行結果の取得に失敗: {}", e)))?;

        // コンテナの停止
        DockerRunnerTrait::stop(&mut docker_runner).await
            .map_err(|e| ContestError::Docker(format!("コンテナの停止に失敗: {}", e)))?;

        Ok(output)
    }
} 