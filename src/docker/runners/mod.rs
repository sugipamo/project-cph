use tokio::sync::Mutex;
use std::sync::Arc;
use bollard::Docker;
use std::time::{Duration, Instant};
use tokio::time::sleep;
use tokio::time::timeout;
use futures::future::join_all;

use crate::docker::{DockerRunner, RunnerState};
use crate::config::Config;

const MAX_BUFFER_SIZE: usize = 1024 * 1024;  // 1MB
const OPERATION_TIMEOUT: Duration = Duration::from_secs(15);  // 15秒に延長
const STOP_TIMEOUT: Duration = Duration::from_secs(10);  // 停止処理用のタイムアウト

struct RunnersState {
    state: RunnerState,
    start_time: Option<Instant>,
    execution_time: Option<Duration>,
}

impl RunnersState {
    fn new() -> Self {
        Self {
            state: RunnerState::Ready,
            start_time: None,
            execution_time: None,
        }
    }

    fn start(&mut self) {
        self.state = RunnerState::Running;
        self.start_time = Some(Instant::now());
    }

    fn stop(&mut self) {
        self.state = RunnerState::Stop;
        self.set_execution_time();
    }

    fn error(&mut self) {
        self.state = RunnerState::Error;
        self.set_execution_time();
    }

    fn set_execution_time(&mut self) {
        if let Some(start) = self.start_time {
            self.execution_time = Some(start.elapsed());
        }
    }
}

pub struct DockerRunners {
    docker: Docker,
    config: Arc<Config>,
    runners: Arc<Mutex<Vec<Arc<Mutex<DockerRunner>>>>>,
    connections: Arc<Mutex<Vec<Vec<usize>>>>,
    state: Arc<Mutex<RunnersState>>,
}

impl DockerRunners {
    pub fn new(docker: Docker, config: Config) -> Self {
        Self {
            docker,
            config: Arc::new(config),
            runners: Arc::new(Mutex::new(Vec::new())),
            connections: Arc::new(Mutex::new(Vec::new())),
            state: Arc::new(Mutex::new(RunnersState::new())),
        }
    }

    pub async fn add_runner(&self, language: String) -> Result<usize, String> {
        let mut runners = self.runners.lock().await;
        let mut connections = self.connections.lock().await;
        let id = runners.len();

        // 言語の存在確認
        let _resolved_lang = self.config.get_with_alias::<String>(&format!("{}.name", language))
            .map_err(|e| format!("言語名の解決に失敗しました: {}", e))?;

        let runner = DockerRunner::new(self.docker.clone(), self.config.clone(), language);
        runners.push(Arc::new(Mutex::new(runner)));
        connections.push(Vec::new());
        Ok(id)
    }

    pub async fn connect(&self, from: usize, to: usize) -> Result<(), String> {
        let mut connections = self.connections.lock().await;
        if from >= connections.len() || to >= connections.len() {
            return Err(format!("無効なランナーID: from={}, to={}", from, to));
        }
        connections[from].push(to);
        Ok(())
    }

    async fn get_runner(&self, id: usize) -> Option<Arc<Mutex<DockerRunner>>> {
        let runners = self.runners.lock().await;
        runners.get(id).cloned()
    }

    pub async fn run_code(&self, id: usize, source_code: &str) -> Result<(), String> {
        let runner = match self.get_runner(id).await {
            Some(runner) => runner,
            None => {
                return Err(format!("ランナー {} が見つかりません", id));
            }
        };
        let mut runner = runner.lock().await;
        runner.run_in_docker(source_code).await
    }

    async fn check_runners(&self, target_state: Option<RunnerState>) -> bool {
        let runners = self.runners.lock().await;
        for (id, runner) in runners.iter().enumerate() {
            println!("Checking runner {} state", id);
            match timeout(OPERATION_TIMEOUT, async {
                let runner = runner.lock().await;
                runner.get_state().await
            }).await {
                Ok(state) => {
                    println!("Runner {} state: {:?}", id, state);
                    match target_state {
                        Some(target) if state != target => {
                            println!("Runner {} state mismatch: expected {:?}, got {:?}", id, target, state);
                            return false;
                        }
                        None if state == RunnerState::Error => {
                            println!("Runner {} in error state", id);
                            return false;
                        }
                        _ => continue,
                    }
                }
                Err(_) => {
                    println!("Timeout checking runner {} state", id);
                    continue;
                }
            }
        }
        true
    }

    async fn forward_outputs(&self) -> Result<(), String> {
        let runners = self.runners.lock().await;
        let runner_count = runners.len();
        drop(runners);

        for from in 0..runner_count {
            let to_runners = {
                let connections = self.connections.lock().await;
                connections.get(from).map(|v| v.clone()).unwrap_or_default()
            };

            if to_runners.is_empty() {
                continue;
            }

            match timeout(OPERATION_TIMEOUT, async {
                if let Some(from_runner) = self.get_runner(from).await {
                    let runner = from_runner.lock().await;
                    let output = runner.read().await?;
                    if output.len() > MAX_BUFFER_SIZE {
                        return Err("出力が大きすぎます".to_string());
                    }
                    let output = output.trim().to_string();
                    for to in to_runners {
                        if let Some(to_runner) = self.get_runner(to).await {
                            let runner = to_runner.lock().await;
                            runner.write(&format!("{}\n", output)).await?;
                        }
                    }
                }
                Ok(())
            }).await {
                Ok(result) => result?,
                Err(_) => {
                    println!("Timeout in forward_outputs for runner {}", from);
                }
            }
        }
        Ok(())
    }

    pub async fn stop_all(&self) -> Result<(), String> {
        println!("Stopping all runners");
        let runners = self.runners.lock().await;
        let stop_futures: Vec<_> = runners.iter().enumerate().map(|(id, runner)| {
            let runner = runner.clone();
            async move {
                println!("Attempting to stop runner {}", id);
                match timeout(STOP_TIMEOUT, async {
                    let mut runner = runner.lock().await;
                    runner.stop().await
                }).await {
                    Ok(_) => println!("Successfully stopped runner {}", id),
                    Err(_) => {
                        println!("Timeout stopping runner {}", id);
                        let mut runner = runner.lock().await;
                        runner.force_stop().await;
                    }
                }
            }
        }).collect();

        join_all(stop_futures).await;
        println!("All runners stop attempted");
        Ok(())
    }

    pub async fn run(&self) -> Result<(), String> {
        println!("Starting runner execution");
        {
            let mut state = self.state.lock().await;
            if state.state != RunnerState::Ready {
                return Err("実行準備ができていません".to_string());
            }
            state.start();
        }

        // タイムアウト設定の取得
        let timeout_seconds = self.config.get::<u64>("system.docker.timeout_seconds")
            .map_err(|e| format!("タイムアウト設定の読み込みに失敗しました: {}", e))?;
        let timeout = Duration::from_secs(timeout_seconds);
        let start = Instant::now();

        loop {
            if start.elapsed() > timeout {
                println!("Execution timeout reached after {:?}", start.elapsed());
                let mut state = self.state.lock().await;
                state.error();
                return Err(format!("実行がタイムアウトしました: {:?}", timeout));
            }

            if !self.check_runners(None).await {
                println!("Runner error detected");
                let mut state = self.state.lock().await;
                state.error();
                return Err("ランナーでエラーが発生しました".to_string());
            }

            self.forward_outputs().await?;
            sleep(Duration::from_millis(100)).await;
        }
    }

    pub async fn get_state(&self) -> RunnerState {
        self.state.lock().await.state.clone()
    }

    pub async fn get_execution_time(&self) -> Option<Duration> {
        self.state.lock().await.execution_time
    }
} 