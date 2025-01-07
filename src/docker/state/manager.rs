use std::sync::Arc;
use std::time::{SystemTime, Duration};
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
    state: Arc<ContainerState>,
    history: Arc<Vec<StateTransitionInfo>>,
}

impl ContainerStateManager {
    pub fn new() -> Self {
        Self {
            state: Arc::new(ContainerState::new()),
            history: Arc::new(Vec::new()),
        }
    }

    pub fn get_current_state(&self) -> ContainerState {
        (*self.state).clone()
    }

    pub fn get_transition_history(&self) -> Vec<StateTransitionInfo> {
        (*self.history).clone()
    }

    fn create_new_manager(&self, new_state: ContainerState, transition_info: StateTransitionInfo) -> Self {
        let new_history = Arc::new({
            let mut history = Vec::with_capacity(self.history.len() + 1);
            history.extend_from_slice(&self.history);
            history.push(transition_info);
            history
        });
        
        Self {
            state: Arc::new(new_state),
            history: new_history,
        }
    }

    async fn validate_transition(&self, transition: &StateTransition) -> Result<()> {
        match transition {
            StateTransition::Create(_) => {
                if !matches!(*self.state, ContainerState::Initial) {
                    return Err(state_err(
                        "状態遷移",
                        "コンテナの作成は初期状態からのみ可能です"
                    ));
                }
            }
            StateTransition::Start => {
                if !matches!(*self.state, ContainerState::Created { .. }) {
                    return Err(state_err(
                        "状態遷移",
                        "コンテナの開始は作成済み状態からのみ可能です"
                    ));
                }
            }
            StateTransition::Execute(_) => {
                if !matches!(*self.state, ContainerState::Running { .. }) {
                    return Err(state_err(
                        "状態遷移",
                        "コマンドの実行は実行中状態からのみ可能です"
                    ));
                }
            }
            StateTransition::Stop => {
                if !matches!(*self.state, ContainerState::Running { .. } | ContainerState::Executing { .. }) {
                    return Err(state_err(
                        "状態遷移",
                        "コンテナの停止は実行中または実行中（コマンド）状態からのみ可能です"
                    ));
                }
            }
            StateTransition::Fail(_) => {
                if matches!(*self.state, ContainerState::Failed { .. } | ContainerState::Stopped { .. }) {
                    return Err(state_err(
                        "状態遷移",
                        "既に失敗または停止状態のコンテナは失敗状態に遷移できません"
                    ));
                }
            }
            StateTransition::Regenerate => {
                if !self.state.can_regenerate() {
                    return Err(state_err(
                        "状態遷移",
                        "現在の状態からは再生成できません"
                    ));
                }
            }
            StateTransition::Restore(_) => {
                // リストア操作は任意の状態から可能
            }
        };
        Ok(())
    }

    pub async fn apply_transition(&self, transition: StateTransition) -> Result<Self> {
        let start_time = SystemTime::now();

        // 状態遷移の検証
        if let Err(e) = self.validate_transition(&transition).await {
            let duration = start_time.elapsed().unwrap_or(Duration::from_secs(0));
            let transition_info = StateTransitionInfo {
                timestamp: start_time,
                transition: transition.clone(),
                result: TransitionResult::Failure(e.to_string()),
                duration,
            };
            return Ok(self.create_new_manager((*self.state).clone(), transition_info));
        }

        let new_state = match transition.clone() {
            StateTransition::Create(container_id) => {
                ContainerState::create(container_id)
            },
            StateTransition::Start => {
                self.state.start()
                    .ok_or_else(|| state_err(
                        "状態遷移",
                        format!("開始遷移の失敗: {}", self.state)
                    ))?
            },
            StateTransition::Execute(command) => {
                self.state.execute(command)
                    .ok_or_else(|| state_err(
                        "状態遷移",
                        format!("コマンド実行遷移の失敗: {}", self.state)
                    ))?
            },
            StateTransition::Stop => {
                self.state.stop()
                    .ok_or_else(|| state_err(
                        "状態遷移",
                        format!("停止遷移の失敗: {}", self.state)
                    ))?
            },
            StateTransition::Fail(error) => {
                self.state.fail(error)
                    .ok_or_else(|| state_err(
                        "状態遷移",
                        format!("失敗遷移の失敗: {}", self.state)
                    ))?
            },
            StateTransition::Regenerate => {
                self.state.regenerate()
                    .ok_or_else(|| state_err(
                        "状態遷移",
                        format!("再生成遷移の失敗: {}", self.state)
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
        let transition_info = StateTransitionInfo {
            timestamp: start_time,
            transition,
            result: TransitionResult::Success(new_state.clone()),
            duration,
        };

        Ok(self.create_new_manager(new_state, transition_info))
    }

    // 公開APIメソッド
    pub async fn create_container(&self, container_id: String) -> Result<Self> {
        self.apply_transition(StateTransition::Create(container_id)).await
    }

    pub async fn start_container(&self) -> Result<Self> {
        self.apply_transition(StateTransition::Start).await
    }

    pub async fn execute_command(&self, command: String) -> Result<Self> {
        self.apply_transition(StateTransition::Execute(command)).await
    }

    pub async fn stop_container(&self) -> Result<Self> {
        self.apply_transition(StateTransition::Stop).await
    }

    pub async fn fail_container(&self, error: String) -> Result<Self> {
        self.apply_transition(StateTransition::Fail(error)).await
    }

    pub async fn regenerate_container(&self) -> Result<Self> {
        self.apply_transition(StateTransition::Regenerate).await
    }

    pub async fn restore_container(&self, state_info: StateInfo) -> Result<Self> {
        self.apply_transition(StateTransition::Restore(state_info)).await
    }

    pub fn get_last_transition(&self) -> Option<StateTransitionInfo> {
        self.history.last().cloned()
    }

    pub fn get_transitions_since(&self, since: SystemTime) -> Vec<StateTransitionInfo> {
        self.history
            .iter()
            .filter(|info| info.timestamp >= since)
            .cloned()
            .collect()
    }
} 