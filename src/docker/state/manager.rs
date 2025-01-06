use std::sync::Arc;
use tokio::sync::{Mutex, mpsc};
use crate::docker::state::types::{ContainerState, StateError};
use crate::docker::state::validation::validate_transition;

pub struct ContainerStateManager {
    state: Arc<Mutex<ContainerState>>,
    container_id: Arc<Mutex<Option<String>>>,
    subscribers: Arc<Mutex<Vec<mpsc::Sender<ContainerState>>>>,
}

impl ContainerStateManager {
    pub fn new() -> Self {
        Self {
            state: Arc::new(Mutex::new(ContainerState::Initial)),
            container_id: Arc::new(Mutex::new(None)),
            subscribers: Arc::new(Mutex::new(Vec::new())),
        }
    }

    pub async fn set_container_id(&self, id: String) {
        let mut container_id = self.container_id.lock().await;
        *container_id = Some(id);
    }

    pub async fn get_container_id(&self) -> Option<String> {
        let container_id = self.container_id.lock().await;
        container_id.clone()
    }

    pub async fn transition_to(&self, new_state: ContainerState) -> Result<(), StateError> {
        let mut state = self.state.lock().await;
        
        // 状態遷移の検証
        validate_transition(&state, &new_state).await?;
        
        // 状態を更新
        *state = new_state.clone();
        
        // 購読者に通知
        self.notify_subscribers(new_state).await;
        
        Ok(())
    }

    async fn notify_subscribers(&self, state: ContainerState) {
        let mut subscribers = self.subscribers.lock().await;
        subscribers.retain_mut(|subscriber| {
            subscriber.try_send(state.clone()).is_ok()
        });
    }

    pub async fn subscribe(&self) -> mpsc::Receiver<ContainerState> {
        let (tx, rx) = mpsc::channel(32);
        let mut subscribers = self.subscribers.lock().await;
        subscribers.push(tx);
        rx
    }

    pub async fn get_current_state(&self) -> ContainerState {
        let state = self.state.lock().await;
        state.clone()
    }
} 