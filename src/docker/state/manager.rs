use std::sync::Arc;
use std::time::{SystemTime, Duration};
use tokio::sync::RwLock;
use crate::error::Result;
use super::ContainerState;
use crate::docker::error::state_err;
use super::types::{StateInfo, StateType};

#[derive(Debug, Clone)]
pub struct StateTransitionInfo {
    pub timestamp: SystemTime,
    pub transition: StateTransition,
    pub result: TransitionResult,
    pub duration: Duration,
}

#[derive(Debug, Clone)]
pub enum TransitionResult {
    Success(ContainerState),
    Failure(String),
}

#[derive(Debug, Clone)]
pub enum StateTransition {
    Create(String),
    Start,
    Execute(String),
    Stop,
    Fail(String),
    Regenerate,
    Restore(StateInfo),
}

#[derive(Debug, Clone)]
pub struct ContainerStateManager {
    state: Arc<RwLock<ContainerState>>,
    history: Arc<RwLock<Vec<StateTransitionInfo>>>,
}

impl ContainerStateManager {
    pub fn new() -> Self {
        Self {
            state: Arc::new(RwLock::new(ContainerState::new())),
            history: Arc::new(RwLock::new(Vec::new())),
        }
    }

    pub async fn get_current_state(&self) -> ContainerState {
        self.state.read().await.clone()
    }

    pub async fn get_transition_history(&self) -> Vec<StateTransitionInfo> {
        self.history.read().await.clone()
    }

    async fn record_transition(&self, transition: StateTransition, result: TransitionResult, duration: Duration) {
        let info = StateTransitionInfo {
            timestamp: SystemTime::now(),
            transition,
            result,
            duration,
        };
        self.history.write().await.push(info);
    }

    async fn validate_transition(&self, transition: &StateTransition, current_state: &ContainerState) -> Result<()> {
        match (current_state, transition) {
            (ContainerState::Initial, StateTransition::Create(_)) => Ok(()),
            (ContainerState::Created { .. }, StateTransition::Start) => Ok(()),
            (ContainerState::Running { .. }, StateTransition::Execute(_)) => Ok(()),
            (ContainerState::Running { .. } | ContainerState::Executing { .. }, StateTransition::Stop) => Ok(()),
            (_, StateTransition::Fail(_)) => Ok(()),
            (ContainerState::Failed { .. }, StateTransition::Regenerate) => Ok(()),
            (ContainerState::Created { .. }, StateTransition::Restore(_)) => Ok(()),
            _ => Err(state_err(
                "状態遷移の検証",
                format!("無効な状態遷移: {} -> {:?}", current_state, transition)
            )),
        }
    }

    async fn apply_transition(&self, transition: StateTransition) -> Result<()> {
        let start_time = SystemTime::now();
        let current_state = self.get_current_state().await;

        // 状態遷移の検証
        if let Err(e) = self.validate_transition(&transition, &current_state).await {
            let duration = start_time.elapsed().unwrap_or(Duration::from_secs(0));
            self.record_transition(
                transition,
                TransitionResult::Failure(e.to_string()),
                duration
            ).await;
            return Err(e);
        }

        let new_state = match transition.clone() {
            StateTransition::Create(container_id) => {
                ContainerState::create(container_id)
            },
            StateTransition::Start => {
                current_state.start()
                    .ok_or_else(|| state_err(
                        "状態遷移",
                        format!("開始遷移の失敗: {}", current_state)
                    ))?
            },
            StateTransition::Execute(command) => {
                current_state.execute(command)
                    .ok_or_else(|| state_err(
                        "状態遷移",
                        format!("コマンド実行遷移の失敗: {}", current_state)
                    ))?
            },
            StateTransition::Stop => {
                current_state.stop()
                    .ok_or_else(|| state_err(
                        "状態遷移",
                        format!("停止遷移の失敗: {}", current_state)
                    ))?
            },
            StateTransition::Fail(error) => {
                current_state.fail(error)
                    .ok_or_else(|| state_err(
                        "状態遷移",
                        format!("失敗遷移の失敗: {}", current_state)
                    ))?
            },
            StateTransition::Regenerate => {
                current_state.regenerate()
                    .ok_or_else(|| state_err(
                        "状態遷移",
                        format!("再生成遷移の失敗: {}", current_state)
                    ))?
            },
            StateTransition::Restore(state_info) => {
                match state_info.state_type {
                    StateType::Running => ContainerState::Running {
                        container_id: state_info.container_id,
                        started_at: state_info.timestamp,
                    },
                    StateType::Executing(command) => ContainerState::Executing {
                        container_id: state_info.container_id,
                        started_at: state_info.timestamp,
                        command,
                    },
                    StateType::Stopped => ContainerState::Stopped {
                        container_id: state_info.container_id,
                        stopped_at: state_info.timestamp,
                        exit_status: None,
                    },
                    StateType::Failed(error) => ContainerState::Failed {
                        container_id: state_info.container_id,
                        error,
                        occurred_at: state_info.timestamp,
                    },
                }
            },
        };

        let duration = start_time.elapsed().unwrap_or(Duration::from_secs(0));
        *self.state.write().await = new_state.clone();
        self.record_transition(
            transition,
            TransitionResult::Success(new_state),
            duration
        ).await;
        Ok(())
    }

    // 公開APIメソッド
    pub async fn create_container(&self, container_id: String) -> Result<()> {
        self.apply_transition(StateTransition::Create(container_id)).await
    }

    pub async fn start_container(&self) -> Result<()> {
        self.apply_transition(StateTransition::Start).await
    }

    pub async fn execute_command(&self, command: String) -> Result<()> {
        self.apply_transition(StateTransition::Execute(command)).await
    }

    pub async fn stop_container(&self) -> Result<()> {
        self.apply_transition(StateTransition::Stop).await
    }

    pub async fn fail_container(&self, error: String) -> Result<()> {
        self.apply_transition(StateTransition::Fail(error)).await
    }

    pub async fn regenerate_container(&self) -> Result<()> {
        self.apply_transition(StateTransition::Regenerate).await
    }

    pub async fn restore_state(&self, state_info: StateInfo) -> Result<()> {
        self.apply_transition(StateTransition::Restore(state_info)).await
    }

    pub async fn get_container_id(&self) -> Result<String> {
        let state = self.get_current_state().await;
        state.container_id()
            .map(String::from)
            .ok_or_else(|| state_err("状態管理", "コンテナIDが見つかりません"))
    }

    pub async fn get_last_transition(&self) -> Option<StateTransitionInfo> {
        self.history.read().await.last().cloned()
    }

    pub async fn get_transitions_since(&self, since: SystemTime) -> Vec<StateTransitionInfo> {
        self.history.read().await
            .iter()
            .filter(|info| info.timestamp >= since)
            .cloned()
            .collect()
    }
} 