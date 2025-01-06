use std::fmt;
use std::time::{Duration, Instant};
use tokio::sync::mpsc;
use crate::docker::error::DockerResult;

#[derive(Debug, Clone, PartialEq)]
pub enum ContainerState {
    /// 初期状態
    Initial,
    /// コンテナが作成された状態
    Created {
        container_id: String,
    },
    /// コンテナが実行中の状態
    Running {
        container_id: String,
        start_time: Instant,
    },
    /// コンテナが停止した状態
    Stopped {
        container_id: String,
        exit_code: i32,
        execution_time: Duration,
    },
    /// エラーが発生した状態
    Failed {
        error: String,
    },
}

impl fmt::Display for ContainerState {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            ContainerState::Initial => write!(f, "初期状態"),
            ContainerState::Created { container_id } => {
                write!(f, "コンテナ作成済み (ID: {})", container_id)
            }
            ContainerState::Running { container_id, start_time } => {
                write!(
                    f,
                    "実行中 (ID: {}, 経過時間: {:?})",
                    container_id,
                    start_time.elapsed()
                )
            }
            ContainerState::Stopped {
                container_id,
                exit_code,
                execution_time,
            } => {
                write!(
                    f,
                    "停止 (ID: {}, 終了コード: {}, 実行時間: {:?})",
                    container_id, exit_code, execution_time
                )
            }
            ContainerState::Failed { error } => {
                write!(f, "エラー: {}", error)
            }
        }
    }
}

pub struct StateManager {
    current_state: ContainerState,
    subscribers: Vec<mpsc::Sender<ContainerState>>,
}

impl StateManager {
    pub fn new() -> Self {
        Self {
            current_state: ContainerState::Initial,
            subscribers: Vec::new(),
        }
    }

    pub async fn transition_to(&mut self, new_state: ContainerState) -> DockerResult<()> {
        self.current_state = new_state.clone();
        
        // 状態変更を購読者に通知
        let mut failed_subscribers = Vec::new();
        for (index, subscriber) in self.subscribers.iter().enumerate() {
            if subscriber.send(new_state.clone()).await.is_err() {
                failed_subscribers.push(index);
            }
        }

        // 切断された購読者を削除
        for index in failed_subscribers.into_iter().rev() {
            self.subscribers.swap_remove(index);
        }

        Ok(())
    }

    pub fn get_current_state(&self) -> &ContainerState {
        &self.current_state
    }

    pub async fn subscribe(&mut self) -> mpsc::Receiver<ContainerState> {
        let (tx, rx) = mpsc::channel(8);
        self.subscribers.push(tx);
        rx
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use tokio::time::sleep;

    #[tokio::test]
    async fn test_state_transitions() {
        let mut manager = StateManager::new();
        assert_eq!(*manager.get_current_state(), ContainerState::Initial);

        // Created状態への遷移
        let created_state = ContainerState::Created {
            container_id: "test_container".to_string(),
        };
        manager.transition_to(created_state.clone()).await.unwrap();
        assert_eq!(*manager.get_current_state(), created_state);

        // Running状態への遷移
        let running_state = ContainerState::Running {
            container_id: "test_container".to_string(),
            start_time: Instant::now(),
        };
        manager.transition_to(running_state.clone()).await.unwrap();
        assert_eq!(
            match manager.get_current_state() {
                ContainerState::Running { container_id, .. } => container_id.as_str(),
                _ => "",
            },
            "test_container"
        );
    }

    #[tokio::test]
    async fn test_state_subscription() {
        let mut manager = StateManager::new();
        let mut rx = manager.subscribe().await;

        // 状態変更を非同期で監視
        let monitor_handle = tokio::spawn(async move {
            let state = rx.recv().await.unwrap();
            matches!(state, ContainerState::Created { .. })
        });

        // 状態を変更
        let new_state = ContainerState::Created {
            container_id: "test_container".to_string(),
        };
        manager.transition_to(new_state).await.unwrap();

        // 監視タスクの結果を確認
        assert!(monitor_handle.await.unwrap());
    }
} 