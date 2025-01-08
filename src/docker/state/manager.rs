use std::sync::Arc;
use std::time::{SystemTime, Duration};
use anyhow::{Result, anyhow};
use super::State;
use super::container_state::{StateInfo, StateType};

#[derive(Debug, Clone)]
pub struct StateTransitionInfo {
    pub timestamp: SystemTime,
    pub transition: StateTransition,
    pub result: TransitionResult,
    pub duration: Duration,
}

#[derive(Debug, Clone)]
pub enum TransitionResult {
    Success(State),
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
pub struct Manager {
    state: Arc<State>,
    history: Arc<Vec<StateTransitionInfo>>,
}

impl Default for Manager {
    fn default() -> Self {
        Self::new()
    }
}

impl Manager {
    #[must_use]
    #[allow(clippy::missing_const_for_fn)]
    pub fn new() -> Self {
        Self {
            state: Arc::new(State::new()),
            history: Arc::new(Vec::new()),
        }
    }

    #[must_use]
    pub fn get_current_state(&self) -> State {
        (*self.state).clone()
    }

    #[must_use]
    pub fn get_transition_history(&self) -> Vec<StateTransitionInfo> {
        (*self.history).clone()
    }

    fn create_new_manager(&self, new_state: State, transition_info: StateTransitionInfo) -> Self {
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

    fn validate_transition(&self, transition: &StateTransition) -> Result<()> {
        match transition {
            StateTransition::Create(_) => {
                if !matches!(*self.state, State::Initial) {
                    return Err(anyhow!("状態遷移エラー: コンテナの作成は初期状態からのみ可能です"));
                }
            }
            StateTransition::Start => {
                if !matches!(*self.state, State::Created { .. }) {
                    return Err(anyhow!("状態遷移エラー: コンテナの開始は作成済み状態からのみ可能です"));
                }
            }
            StateTransition::Execute(_) => {
                if !matches!(*self.state, State::Running { .. }) {
                    return Err(anyhow!("状態遷移エラー: コマンドの実行は実行中状態からのみ可能です"));
                }
            }
            StateTransition::Stop => {
                if !matches!(*self.state, State::Running { .. } | State::Executing { .. }) {
                    return Err(anyhow!("状態遷移エラー: コンテナの停止は実行中または実行中（コマンド）状態からのみ可能です"));
                }
            }
            StateTransition::Fail(_) => {
                if matches!(*self.state, State::Failed { .. } | State::Stopped { .. }) {
                    return Err(anyhow!("状態遷移エラー: 既に失敗または停止状態のコンテナは失敗状態に遷移できません"));
                }
            }
            StateTransition::Regenerate => {
                if !self.state.can_regenerate() {
                    return Err(anyhow!("状態遷移エラー: 現在の状態からは再生成できません"));
                }
            }
            StateTransition::Restore(_) => {
                // リストア操作は任意の状態から可能
            }
        };
        Ok(())
    }

    /// コンテナの状態移を適用します。
    /// 
    /// # Errors
    /// - 無効な状態遷移が要求された場合
    /// - 状態遷移の実行に失敗した場合
    pub fn apply_transition(&self, transition: StateTransition) -> Result<Self> {
        let start_time = SystemTime::now();

        // 状態遷移の検証
        if let Err(e) = self.validate_transition(&transition) {
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
                State::create(container_id)
            },
            StateTransition::Start => {
                self.state.start()
                    .ok_or_else(|| anyhow!("状態遷移エラー: 開始遷移の失敗: {}", self.state))?
            },
            StateTransition::Execute(command) => {
                self.state.execute(command)
                    .ok_or_else(|| anyhow!("状態遷移エラー: コマンド実行遷移の失敗: {}", self.state))?
            },
            StateTransition::Stop => {
                self.state.stop()
                    .ok_or_else(|| anyhow!("状態遷移エラー: 停止遷移の失敗: {}", self.state))?
            },
            StateTransition::Fail(error) => {
                self.state.fail(error)
                    .ok_or_else(|| anyhow!("状態遷移エラー: 失敗遷移の失敗: {}", self.state))?
            },
            StateTransition::Regenerate => {
                self.state.regenerate()
                    .ok_or_else(|| anyhow!("状態遷移エラー: 再生成遷移の失敗: {}", self.state))?
            },
            StateTransition::Restore(state_info) => {
                match state_info.state_type {
                    StateType::Running => State::Running {
                        container_id: state_info.container_id,
                        started_at: state_info.timestamp,
                    },
                    StateType::Executing(command) => State::Executing {
                        container_id: state_info.container_id,
                        started_at: state_info.timestamp,
                        command,
                    },
                    StateType::Stopped => State::Stopped {
                        container_id: state_info.container_id,
                        stopped_at: state_info.timestamp,
                        exit_status: None,
                    },
                    StateType::Failed(error) => State::Failed {
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

    /// 新しいコンテナを作成します。
    /// 
    /// # Errors
    /// - コンテナが既に存在する場合
    pub fn create_container(&self, container_id: String) -> Result<Self> {
        self.apply_transition(StateTransition::Create(container_id))
    }

    /// コンテナを開始します。
    /// 
    /// # Errors
    /// - コンテナが作成済み状態でない場合
    pub fn start_container(&self) -> Result<Self> {
        self.apply_transition(StateTransition::Start)
    }

    /// コンテナ内でコマンドを実行します。
    /// 
    /// # Errors
    /// - コンテナが実行中状態でない場合
    pub fn execute_command(&self, command: String) -> Result<Self> {
        self.apply_transition(StateTransition::Execute(command))
    }

    /// コンテナを停止します。
    /// 
    /// # Errors
    /// - コンテナが実行中または実行中（コマンド）状態でない場合
    pub fn stop_container(&self) -> Result<Self> {
        self.apply_transition(StateTransition::Stop)
    }

    /// コンテナを失敗状態に遷移させます。
    /// 
    /// # Errors
    /// - コンテナが既に失敗または停止状態の場合
    pub fn fail_container(&self, error: String) -> Result<Self> {
        self.apply_transition(StateTransition::Fail(error))
    }

    /// コンテナを再生成します。
    /// 
    /// # Errors
    /// - 現在の状態から再生成が不可能な場合
    pub fn regenerate_container(&self) -> Result<Self> {
        self.apply_transition(StateTransition::Regenerate)
    }

    /// コンテナの状態を復元します。
    /// 
    /// # Errors
    /// - 状態の復元に失敗した場合
    pub fn restore_container(&self, state_info: StateInfo) -> Result<Self> {
        self.apply_transition(StateTransition::Restore(state_info))
    }

    #[must_use]
    pub fn get_last_transition(&self) -> Option<StateTransitionInfo> {
        self.history.last().cloned()
    }

    #[must_use]
    pub fn get_transitions_since(&self, since: SystemTime) -> Vec<StateTransitionInfo> {
        self.history
            .iter()
            .filter(|info| info.timestamp >= since)
            .cloned()
            .collect()
    }
} 