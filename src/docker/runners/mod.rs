use tokio::sync::Mutex;
use std::sync::Arc;
use bollard::Docker;
use std::time::{Duration, Instant};
use tokio::time::sleep;

use crate::docker::{DockerRunner, RunnerConfig, DockerError, RunnerState};
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
    /// Runnersの状態
    state: Arc<Mutex<RunnerState>>,
    /// 実行時間の計測
    execution_time: Arc<Mutex<Option<Duration>>>,
}

impl DockerRunners {
    /// 新しいDockerRunnersインスタンスを作成
    pub fn new(docker: Docker, config: RunnerConfig) -> Self {
        Self {
            docker,
            config,
            runners: Arc::new(Mutex::new(Vec::new())),
            connections: Arc::new(Mutex::new(Vec::new())),
            state: Arc::new(Mutex::new(RunnerState::Ready)),
            execution_time: Arc::new(Mutex::new(None)),
        }
    }

    /// 現在の状態を取得
    pub async fn get_state(&self) -> RunnerState {
        self.state.lock().await.clone()
    }

    /// 実行時間を取得
    pub async fn get_execution_time(&self) -> Option<Duration> {
        self.execution_time.lock().await.clone()
    }

    /// 全てのRunnerの状態をチェック
    async fn check_all_runners_state(&self) -> Result<bool> {
        let runners = self.runners.lock().await;
        for runner in runners.iter() {
            let runner = runner.lock().await;
            if runner.get_state().await == RunnerState::Error {
                return Ok(false);
            }
        }
        Ok(true)
    }

    /// 全てのRunnerが指定した状態になるまで待機
    async fn wait_for_all_runners_state(&self, target_state: RunnerState) -> Result<bool> {
        let runners = self.runners.lock().await;
        for runner in runners.iter() {
            let runner = runner.lock().await;
            if runner.get_state().await != target_state {
                return Ok(false);
            }
        }
        Ok(true)
    }

    /// Runnersを実行
    pub async fn run(&self) -> Result<()> {
        // 状態チェック
        let mut state = self.state.lock().await;
        if *state != RunnerState::Ready {
            return Err(DockerError::InvalidStateTransition {
                from: state.to_string(),
                to: RunnerState::Running.to_string(),
            });
        }
        *state = RunnerState::Running;
        drop(state);

        let start_time = Instant::now();
        let timeout_duration = Duration::from_secs(5);
        let mut execution_completed = false;

        // 全てのRunnerが実行状態になるまで待機
        while !self.wait_for_all_runners_state(RunnerState::Running).await? {
            if start_time.elapsed() > timeout_duration {
                *self.state.lock().await = RunnerState::Error;
                self.stop_all().await?;
                return Err(DockerError::RuntimeError("Timeout waiting for runners to start".to_string()));
            }
            sleep(Duration::from_millis(100)).await;
        }

        // メインループ
        while !execution_completed {
            // タイムアウトチェック
            if start_time.elapsed() > timeout_duration {
                *self.state.lock().await = RunnerState::Error;
                self.stop_all().await?;
                return Err(DockerError::RuntimeError("Execution timeout".to_string()));
            }

            // エラーチェック
            if !self.check_all_runners_state().await? {
                *self.state.lock().await = RunnerState::Error;
                *self.execution_time.lock().await = Some(start_time.elapsed());
                self.stop_all().await?;
                return Err(DockerError::RuntimeError("Runner error detected".to_string()));
            }

            // 全Runnerの出力を転送
            let runners = self.runners.lock().await;
            for id in 0..runners.len() {
                if let Err(e) = self.forward_output(id).await {
                    println!("Warning: Failed to forward output from runner {}: {:?}", id, e);
                }
            }

            // 全てのRunnerが停止状態かチェック
            if self.wait_for_all_runners_state(RunnerState::Stop).await? {
                execution_completed = true;
            } else {
                sleep(Duration::from_millis(100)).await;
            }
        }

        // 実行完了
        *self.state.lock().await = RunnerState::Stop;
        *self.execution_time.lock().await = Some(start_time.elapsed());
        Ok(())
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