use std::sync::Arc;
use anyhow::{Result, anyhow};
use tokio::sync::{oneshot, Mutex};
use super::Runtime;
use super::config::Config;

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum State {
    Created,
    Running,
    Completed,
    Failed(String),
}

pub struct Container {
    config: Config,
    runtime: Arc<dyn Runtime>,
    state: Arc<Mutex<State>>,
    cancel_tx: Option<Arc<oneshot::Sender<()>>>,
    #[allow(dead_code)]
    cancel_rx: Option<oneshot::Receiver<()>>,
}

impl Container {
    pub fn new(runtime: Arc<dyn Runtime>, config: Config) -> Self {
        Self {
            runtime,
            config,
            state: Arc::new(Mutex::new(State::Created)),
            cancel_tx: None,
            cancel_rx: None,
        }
    }

    /// コンテナを実行します
    /// 
    /// # Errors
    /// - ランタイムの実行に失敗した場合
    /// - 状態の更新に失敗した場合
    pub async fn run(&self) -> Result<()> {
        println!("Container({}): 実行開始", self.id());
        {
            let mut state = self.state.lock().await;
            *state = State::Running;
            drop(state);
        }

        let result = self.runtime.run(&self.config).await;

        if let Err(e) = result {
            println!("Container({}): エラー発生: {}", self.id(), e);
            {
                let mut state = self.state.lock().await;
                *state = State::Failed(e.to_string());
                drop(state);
            }
            return Err(e);
        }

        {
            let mut state = self.state.lock().await;
            *state = State::Completed;
            drop(state);
        }

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
                    tx.send(()).map_err(|_| anyhow!("キャンセルチャネルが閉じられています"))?;
                }
            }
        }

        {
            let mut state = self.state.lock().await;
            *state = State::Completed;
            drop(state);
        }
        Ok(())
    }

    pub async fn status(&self) -> State {
        self.state.lock().await.clone()
    }

    #[must_use]
    pub fn id(&self) -> &str {
        &self.config.id
    }

    pub async fn state(&self) -> State {
        self.state.lock().await.clone()
    }

    /// コンテナの状態を設定します
    /// 
    /// # Errors
    /// - 状態のロックの取得に失敗した場合
    pub async fn set_state(&self, new_state: State) -> Result<()> {
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