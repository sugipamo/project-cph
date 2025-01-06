use std::fmt;
use std::collections::HashMap;
use std::sync::Arc;
use std::time::{Duration, Instant};
use tokio::sync::{Mutex, mpsc};
use crate::docker::error::{DockerError, DockerResult};

#[derive(Debug, Clone, PartialEq)]
pub enum RunnerState {
    Initial,
    Running(ContainerContext),
    Completed(ExecutionResult),
    Failed(RunnerError),
}

#[derive(Debug, Clone, PartialEq)]
pub struct ContainerContext {
    pub container_id: String,
    pub start_time: Instant,
    pub memory_usage: Option<u64>,
    pub status: ContainerStatus,
}

#[derive(Debug, Clone, PartialEq)]
pub enum ContainerStatus {
    Created,
    Running,
    Stopped,
    Failed(String),
}

#[derive(Debug, Clone, PartialEq)]
pub struct ExecutionResult {
    pub exit_code: i32,
    pub execution_time: Duration,
    pub output: String,
}

#[derive(Debug, Clone, PartialEq)]
pub enum RunnerError {
    ContainerCreationFailed(String),
    ContainerStartFailed(String),
    ExecutionTimeout(Duration),
    ResourceExhausted(String),
    InvalidStateTransition(String),
}

#[derive(Debug, Clone)]
pub struct StateChange {
    pub runner_id: String,
    pub previous_state: RunnerState,
    pub new_state: RunnerState,
    pub timestamp: Instant,
}

pub struct RunnerStateManager {
    state: Arc<Mutex<RunnerState>>,
    container_states: Arc<Mutex<HashMap<String, ContainerContext>>>,
    subscribers: Arc<Mutex<Vec<mpsc::Sender<StateChange>>>>,
    runner_id: String,
}

impl RunnerStateManager {
    pub fn new(runner_id: String) -> Self {
        Self {
            state: Arc::new(Mutex::new(RunnerState::Initial)),
            container_states: Arc::new(Mutex::new(HashMap::new())),
            subscribers: Arc::new(Mutex::new(Vec::new())),
            runner_id,
        }
    }

    pub async fn transition_to(&mut self, new_state: RunnerState) -> DockerResult<()> {
        let mut state = self.state.lock().await;
        if state.can_transition_to(&new_state) {
            let previous_state = state.clone();
            *state = new_state.clone();
            
            // 状態変更を通知
            self.notify_state_change(previous_state, new_state).await;
            Ok(())
        } else {
            Err(DockerError::InvalidState(format!(
                "Invalid state transition from {:?} to {:?}",
                *state, new_state
            )))
        }
    }

    pub async fn update_container_state(
        &mut self,
        container_id: String,
        status: ContainerStatus,
    ) -> DockerResult<()> {
        let mut states = self.container_states.lock().await;
        if let Some(context) = states.get_mut(&container_id) {
            context.status = status;
            Ok(())
        } else {
            let context = ContainerContext {
                container_id: container_id.clone(),
                start_time: Instant::now(),
                memory_usage: None,
                status,
            };
            states.insert(container_id, context);
            Ok(())
        }
    }

    pub async fn get_container_state(&self, container_id: &str) -> Option<ContainerContext> {
        let states = self.container_states.lock().await;
        states.get(container_id).cloned()
    }

    pub async fn get_current_state(&self) -> RunnerState {
        self.state.lock().await.clone()
    }

    pub async fn subscribe(&mut self) -> mpsc::Receiver<StateChange> {
        let (tx, rx) = mpsc::channel(100);
        let mut subscribers = self.subscribers.lock().await;
        subscribers.push(tx);
        rx
    }

    async fn notify_state_change(&self, previous_state: RunnerState, new_state: RunnerState) {
        let change = StateChange {
            runner_id: self.runner_id.clone(),
            previous_state,
            new_state,
            timestamp: Instant::now(),
        };

        let subscribers = self.subscribers.lock().await;
        for subscriber in subscribers.iter() {
            let _ = subscriber.send(change.clone()).await;
        }
    }
}

impl RunnerState {
    pub fn is_terminal(&self) -> bool {
        matches!(self, RunnerState::Completed(_) | RunnerState::Failed(_))
    }

    pub fn can_transition_to(&self, next: &RunnerState) -> bool {
        match (self, next) {
            (RunnerState::Initial, RunnerState::Running(_)) => true,
            (RunnerState::Running(_), RunnerState::Completed(_)) => true,
            (RunnerState::Running(_), RunnerState::Failed(_)) => true,
            _ => false,
        }
    }
}

impl From<RunnerError> for RunnerState {
    fn from(error: RunnerError) -> Self {
        RunnerState::Failed(error)
    }
}

impl fmt::Display for RunnerError {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            RunnerError::ContainerCreationFailed(msg) => write!(f, "コンテナの作成に失敗しました: {}", msg),
            RunnerError::ContainerStartFailed(msg) => write!(f, "コンテナの起動に失敗しました: {}", msg),
            RunnerError::ExecutionTimeout(duration) => write!(f, "実行がタイムアウトしました: {:?}", duration),
            RunnerError::ResourceExhausted(msg) => write!(f, "リソースが枯渇しました: {}", msg),
            RunnerError::InvalidStateTransition(msg) => write!(f, "不正な状態遷移です: {}", msg),
        }
    }
} 