use tokio::sync::Mutex;
use std::sync::Arc;
use bollard::Docker;
use std::time::{Duration, Instant};
use tokio::time::sleep;
use tokio::time::timeout;
use futures::future::join_all;

use crate::docker::{DockerRunner, DockerConfig, RunnerState};

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
    config: DockerConfig,
    runners: Arc<Mutex<Vec<Arc<Mutex<DockerRunner>>>>>,
    connections: Arc<Mutex<Vec<Vec<usize>>>>,
    state: Arc<Mutex<RunnersState>>,
}

impl DockerRunners {
    pub fn new(docker: Docker, config: DockerConfig) -> Self {
        Self {
            docker,
            config,
            runners: Arc::new(Mutex::new(Vec::new())),
            connections: Arc::new(Mutex::new(Vec::new())),
            state: Arc::new(Mutex::new(RunnersState::new())),
        }
    }

    pub async fn add_runner(&self, language: String) -> usize {
        let mut runners = self.runners.lock().await;
        let mut connections = self.connections.lock().await;
        let id = runners.len();
        let runner = DockerRunner::new(self.docker.clone(), self.config.clone(), language);
        runners.push(Arc::new(Mutex::new(runner)));
        connections.push(Vec::new());
        id
    }

    pub async fn connect(&self, from: usize, to: usize) -> () {
        let mut connections = self.connections.lock().await;
        if from >= connections.len() || to >= connections.len() {
            println!("Invalid runner id");
            return;
        }
        connections[from].push(to);
    }

    async fn get_runner(&self, id: usize) -> Option<Arc<Mutex<DockerRunner>>> {
        let runners = self.runners.lock().await;
        runners.get(id).cloned()
    }

    pub async fn run_code(&self, id: usize, source_code: &str) -> () {
        let runner = match self.get_runner(id).await {
            Some(runner) => runner,
            None => {
                println!("Runner {} not found", id);
                return;
            }
        };
        let mut runner = runner.lock().await;
        runner.run_in_docker(source_code).await;
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

    async fn forward_outputs(&self) -> () {
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
                    let output = runner.read().await;
                    if output.len() > MAX_BUFFER_SIZE {
                        println!("Output too large");
                        return;
                    }
                    let output = output.trim().to_string();
                    for to in to_runners {
                        if let Some(to_runner) = self.get_runner(to).await {
                            let runner = to_runner.lock().await;
                            runner.write(&format!("{}\n", output)).await;
                        }
                    }
                }
            }).await {
                Ok(_) => (),
                Err(_) => {
                    println!("Timeout in forward_outputs for runner {}", from);
                }
            }
        }
    }

    pub async fn stop_all(&self) -> () {
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
    }

    pub async fn run(&self) -> () {
        println!("Starting runner execution");
        {
            let mut state = self.state.lock().await;
            if state.state != RunnerState::Ready {
                println!("Not in ready state");
                return;
            }
            state.start();
        }

        let timeout = Duration::from_secs(self.config.timeout_seconds);
        let start = Instant::now();

        loop {
            if start.elapsed() > timeout {
                println!("Execution timeout reached after {:?}", start.elapsed());
                let mut state = self.state.lock().await;
                state.error();
                return;
            }

            if !self.check_runners(None).await {
                println!("Runner error detected");
                let mut state = self.state.lock().await;
                state.error();
                return;
            }

            self.forward_outputs().await;
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