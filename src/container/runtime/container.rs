use std::sync::Arc;
use anyhow::Result;
use tokio::sync::{oneshot, Mutex};
use super::Runtime;
use super::config::Config;

#[derive(Debug, Clone, PartialEq)]
pub enum ContainerState {
    Created,
    Running,
    Completed,
    Failed(String),
}

pub struct Container {
    config: Config,
    runtime: Arc<dyn Runtime>,
    state: Arc<Mutex<ContainerState>>,
    cancel_tx: Option<Arc<oneshot::Sender<()>>>,
    #[allow(dead_code)]
    cancel_rx: Option<oneshot::Receiver<()>>,
}

impl Container {
    pub fn new(runtime: Arc<dyn Runtime>, config: Config) -> Self {
        Self {
            runtime,
            config,
            state: Arc::new(Mutex::new(ContainerState::Created)),
            cancel_tx: None,
            cancel_rx: None,
        }
    }

    pub async fn run(&self) -> Result<()> {
        println!("Container({}): 実行開始", self.id());
        let mut state = self.state.lock().await;
        *state = ContainerState::Running;
        println!("Container({}): 状態を Running に変更", self.id());
        drop(state);

        let result = self.runtime.run(&self.config).await;
        
        if let Err(e) = result {
            println!("Container({}): エラー発生: {}", self.id(), e);
            let mut state = self.state.lock().await;
            *state = ContainerState::Failed(e.to_string());
            return Err(e);
        }
        
        let mut state = self.state.lock().await;
        *state = ContainerState::Completed;
        println!("Container({}): 状態を Completed に変更", self.id());
        
        println!("Container({}): 実行完了", self.id());
        Ok(())
    }

    /// コンテナをキャンセルします
    /// 
    /// # Errors
    /// - キャンセル用のチャネルが既に閉じられている場合
    /// - 状態の更新に失敗した場合
    pub async fn cancel(&self) -> Result<()> {
        if let Some(tx) = &self.cancel_tx {
            if Arc::strong_count(tx) == 1 {
                if let Ok(tx) = Arc::try_unwrap(tx.clone()) {
                    let _ = tx.send(());
                }
            }
        }
        
        let mut state = self.state.lock().await;
        *state = ContainerState::Completed;
        Ok(())
    }

    pub async fn status(&self) -> ContainerState {
        self.state.lock().await.clone()
    }

    pub fn id(&self) -> &str {
        &self.config.id
    }

    pub async fn state(&self) -> ContainerState {
        self.state.lock().await.clone()
    }

    /// コンテナの状態を設定します
    /// 
    /// # Errors
    /// - 状態のロックの取得に失敗した場合
    pub async fn set_state(&self, new_state: ContainerState) -> Result<()> {
        *self.state.lock().await = new_state;
        Ok(())
    }
}

impl Clone for Container {
    fn clone(&self) -> Self {
        let (tx, rx) = oneshot::channel();
        Self {
            config: self.config.clone(),
            runtime: self.runtime.clone(),
            state: self.state.clone(),
            cancel_tx: Some(Arc::new(tx)),
            cancel_rx: Some(rx),
        }
    }
} 