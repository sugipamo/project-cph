use std::fmt;
use std::sync::Arc;
use std::time::{Duration, Instant};
use tokio::sync::{Mutex, mpsc};
use crate::docker::error::{DockerError, DockerResult};

#[derive(Debug, Clone, PartialEq)]
pub enum DockerState {
    Initial,
    Created {
        container_id: String,
        created_at: Instant,
    },
    Running {
        container_id: String,
        start_time: Instant,
        memory_usage: Option<u64>,
    },
    Completed {
        container_id: String,
        exit_code: i32,
        execution_time: Duration,
        output: String,
    },
    Failed {
        container_id: Option<String>,
        error: String,
        occurred_at: Instant,
    },
}

#[derive(Debug, Clone)]
pub struct StateChange {
    pub runner_id: String,
    pub previous_state: DockerState,
    pub new_state: DockerState,
    pub timestamp: Instant,
}

pub struct DockerStateManager {
    state: Arc<Mutex<DockerState>>,
    subscribers: Arc<Mutex<Vec<mpsc::Sender<StateChange>>>>,
    runner_id: String,
}

impl DockerStateManager {
    pub fn new(runner_id: String) -> Self {
        Self {
            state: Arc::new(Mutex::new(DockerState::Initial)),
            subscribers: Arc::new(Mutex::new(Vec::new())),
            runner_id,
        }
    }

    pub async fn transition_to(&mut self, new_state: DockerState) -> DockerResult<()> {
        let mut current = self.state.lock().await;
        
        // 状態遷移の検証
        if !self.is_valid_transition(&current, &new_state) {
            return Err(DockerError::InvalidState(format!(
                "Invalid transition from {:?} to {:?}",
                *current, new_state
            )));
        }

        let previous = current.clone();
        *current = new_state.clone();
        
        // 状態変更を通知
        self.notify_state_change(previous, new_state).await;
        Ok(())
    }

    fn is_valid_transition(&self, from: &DockerState, to: &DockerState) -> bool {
        use DockerState::*;
        matches!(
            (from, to),
            (Initial, Created { .. }) |
            (Created { .. }, Running { .. }) |
            (Running { .. }, Completed { .. }) |
            (_, Failed { .. })
        )
    }

    pub async fn get_current_state(&self) -> DockerState {
        self.state.lock().await.clone()
    }

    pub async fn get_container_id(&self) -> Option<String> {
        let state = self.state.lock().await;
        match &*state {
            DockerState::Created { container_id, .. } |
            DockerState::Running { container_id, .. } |
            DockerState::Completed { container_id, .. } => Some(container_id.clone()),
            DockerState::Failed { container_id, .. } => container_id.clone(),
            _ => None,
        }
    }

    pub async fn subscribe(&mut self) -> mpsc::Receiver<StateChange> {
        let (tx, rx) = mpsc::channel(100);
        let mut subscribers = self.subscribers.lock().await;
        subscribers.push(tx);
        rx
    }

    async fn notify_state_change(&self, previous_state: DockerState, new_state: DockerState) {
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

    pub async fn update_memory_usage(&mut self, memory: u64) -> DockerResult<()> {
        let mut current = self.state.lock().await;
        match &*current {
            DockerState::Running { container_id, start_time, .. } => {
                *current = DockerState::Running {
                    container_id: container_id.clone(),
                    start_time: *start_time,
                    memory_usage: Some(memory),
                };
                Ok(())
            }
            _ => Err(DockerError::InvalidState(
                "Memory usage can only be updated in Running state".to_string()
            )),
        }
    }
}

impl DockerState {
    pub fn is_terminal(&self) -> bool {
        matches!(self, DockerState::Completed { .. } | DockerState::Failed { .. })
    }
}

impl fmt::Display for DockerState {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            DockerState::Initial => write!(f, "初期状態"),
            DockerState::Created { container_id, .. } => {
                write!(f, "コンテナ作成済み (ID: {})", container_id)
            }
            DockerState::Running { container_id, memory_usage, .. } => {
                write!(
                    f,
                    "実行中 (ID: {}, メモリ使用量: {})",
                    container_id,
                    memory_usage.map_or("不明".to_string(), |m| format!("{}MB", m))
                )
            }
            DockerState::Completed { container_id, exit_code, execution_time, .. } => {
                write!(
                    f,
                    "完了 (ID: {}, 終了コード: {}, 実行時間: {:?})",
                    container_id, exit_code, execution_time
                )
            }
            DockerState::Failed { container_id, error, .. } => {
                write!(
                    f,
                    "失敗 (ID: {}, エラー: {})",
                    container_id.as_deref().unwrap_or("なし"),
                    error
                )
            }
        }
    }
} 