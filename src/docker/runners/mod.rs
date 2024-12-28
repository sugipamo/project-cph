use std::collections::HashMap;
use tokio::sync::Mutex;
use std::sync::Arc;
use bollard::Docker;

use crate::docker::{DockerRunner, RunnerConfig, DockerError};
use crate::docker::error::Result;

/// 複数のDockerRunnerを管理し、それらの間の通信を制御するための構造体
pub struct DockerRunners {
    /// Docker clientの共有インスタンス
    docker: Docker,
    /// 共有設定
    config: RunnerConfig,
    /// Runner IDとDockerRunnerのマッピング
    runners: Arc<Mutex<HashMap<String, Arc<Mutex<DockerRunner>>>>>,
    /// Runner間の接続情報
    connections: Arc<Mutex<HashMap<String, Vec<String>>>>,
}

impl DockerRunners {
    /// 新しいDockerRunnersインスタンスを作成
    pub fn new(docker: Docker, config: RunnerConfig) -> Self {
        Self {
            docker,
            config,
            runners: Arc::new(Mutex::new(HashMap::new())),
            connections: Arc::new(Mutex::new(HashMap::new())),
        }
    }

    /// 新しいRunnerを追加
    pub async fn add_runner(&self, id: String, language: String) -> Result<()> {
        let mut runners = self.runners.lock().await;
        if runners.contains_key(&id) {
            return Err(DockerError::RuntimeError(format!("Runner with id {} already exists", id)));
        }

        let runner = DockerRunner::new(self.docker.clone(), self.config.clone(), language);
        runners.insert(id, Arc::new(Mutex::new(runner)));
        Ok(())
    }

    /// Runnerを取得
    async fn get_runner(&self, id: &str) -> Result<Arc<Mutex<DockerRunner>>> {
        let runners = self.runners.lock().await;
        runners.get(id)
            .cloned()
            .ok_or_else(|| DockerError::RuntimeError(format!("Runner with id {} not found", id)))
    }

    /// Runner間の接続を設定
    pub async fn connect(&self, from: String, to: String) -> Result<()> {
        let mut connections = self.connections.lock().await;
        connections
            .entry(from)
            .or_insert_with(Vec::new)
            .push(to);
        Ok(())
    }

    /// 指定されたRunnerの出力を接続先のRunnerの入力として転送
    pub async fn forward_output(&self, from: &str) -> Result<()> {
        // 接続情報を取得
        let to_runners = {
            let connections = self.connections.lock().await;
            connections.get(from)
                .ok_or_else(|| DockerError::RuntimeError(format!("No connections found for runner {}", from)))?
                .clone()
        };

        // 出力を取得
        let from_runner = self.get_runner(from).await?;
        let output = {
            let mut runner = from_runner.lock().await;
            runner.read().await?
        };
        let output = output.trim().to_string();

        // 各接続先に出力を転送
        for to in to_runners {
            let to_runner = self.get_runner(&to).await?;
            let mut runner = to_runner.lock().await;
            runner.write(&format!("{}\n", output)).await?;
        }

        Ok(())
    }

    /// 全てのRunnerを停止
    pub async fn stop_all(&self) -> Result<()> {
        let runners = self.runners.lock().await;
        for (id, _) in runners.iter() {
            let runner = self.get_runner(id).await?;
            let mut runner = runner.lock().await;
            runner.stop().await?;
        }
        Ok(())
    }

    /// Runnerでコードを実行
    pub async fn run_code(&self, id: &str, source_code: &str) -> Result<()> {
        let runner = self.get_runner(id).await?;
        let mut runner = runner.lock().await;
        runner.run_in_docker(source_code).await?;
        Ok(())
    }
} 