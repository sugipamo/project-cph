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
    runners: Arc<Mutex<Vec<Arc<Mutex<DockerRunner>>>>>,
    /// Runner間の接続情報（インデックスがfrom_id、値がto_ids）
    connections: Arc<Mutex<Vec<Vec<usize>>>>,
}

impl DockerRunners {
    /// 新しいDockerRunnersインスタンスを作成
    pub fn new(docker: Docker, config: RunnerConfig) -> Self {
        Self {
            docker,
            config,
            runners: Arc::new(Mutex::new(Vec::new())),
            connections: Arc::new(Mutex::new(Vec::new())),
        }
    }

    /// 新しいRunnerを追加（スタックの先頭に追加）
    pub async fn add_runner(&self, language: String) -> Result<usize> {
        let mut runners = self.runners.lock().await;
        let mut connections = self.connections.lock().await;
        let id = runners.len();
        let runner = DockerRunner::new(self.docker.clone(), self.config.clone(), language);
        runners.push(Arc::new(Mutex::new(runner)));
        connections.push(Vec::new());  // 新しいRunnerの接続情報を初期化
        Ok(id)
    }

    /// Runnerを取得（後から追加された方が先に見つかる）
    async fn get_runner(&self, id: usize) -> Result<Arc<Mutex<DockerRunner>>> {
        let runners = self.runners.lock().await;
        runners.get(id)
            .cloned()
            .ok_or_else(|| DockerError::RuntimeError(format!("Runner with id {} not found", id)))
    }

    /// Runner間の接続を設定
    pub async fn connect(&self, from: usize, to: usize) -> Result<()> {
        let mut connections = self.connections.lock().await;
        if from >= connections.len() || to >= connections.len() {
            return Err(DockerError::RuntimeError(format!("Invalid runner id")));
        }
        connections[from].push(to);
        Ok(())
    }

    /// 指定されたRunnerの出力を接続先のRunnerの入力として転送
    pub async fn forward_output(&self, from: usize) -> Result<()> {
        // 接続情報を取得
        let to_runners = {
            let connections = self.connections.lock().await;
            if from >= connections.len() {
                return Err(DockerError::RuntimeError(format!("Invalid runner id: {}", from)));
            }
            connections[from].clone()
        };

        if to_runners.is_empty() {
            return Ok(());  // 接続先がない場合は早期リターン
        }

        // 出力を取得
        let from_runner = self.get_runner(from).await?;
        let output = {
            let mut runner = from_runner.lock().await;
            runner.read().await?
        };
        let output = output.trim().to_string();

        // 各接続先に出力を転送
        for to in to_runners {
            let to_runner = self.get_runner(to).await?;
            let mut runner = to_runner.lock().await;
            runner.write(&format!("{}\n", output)).await?;
        }

        Ok(())
    }

    /// 全てのRunnerを停止（後入れ先出しで停止）
    pub async fn stop_all(&self) -> Result<()> {
        let runners = self.runners.lock().await;
        for (id, runner) in runners.iter().enumerate().rev() {
            let mut runner = runner.lock().await;
            runner.stop().await?;
        }
        Ok(())
    }

    /// Runnerでコードを実行
    pub async fn run_code(&self, id: usize, source_code: &str) -> Result<()> {
        let runner = self.get_runner(id).await?;
        let mut runner = runner.lock().await;
        runner.run_in_docker(source_code).await?;
        Ok(())
    }

    /// 登録されているRunner IDのリストを取得（スタックの順序）
    pub async fn list_runners(&self) -> Vec<usize> {
        let runners = self.runners.lock().await;
        (0..runners.len()).rev().collect()
    }
} 