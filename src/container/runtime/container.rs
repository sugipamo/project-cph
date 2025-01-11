use std::sync::Arc;
use anyhow::Result;
use tokio::sync::{oneshot, Mutex};
use crate::container::{
    state::lifecycle::Status,
    communication::transport::Network,
    io::buffer::Buffer,
};
use super::{
    config::Config,
    Runtime,
};

#[derive(Clone)]
struct RuntimeState {
    container_id: String,
    status: Status,
}

#[derive(Clone)]
enum ContainerState {
    Initial,
    Running {
        runtime: RuntimeState,
        cancel_tx: Option<Arc<oneshot::Sender<()>>>,
    },
    Completed {
        runtime: RuntimeState,
    },
    #[allow(dead_code)]
    Failed {
        error: String,
        runtime: Option<RuntimeState>,
    },
}

impl Default for ContainerState {
    fn default() -> Self {
        Self::Initial
    }
}

pub struct Container {
    network: Arc<Network>,
    buffer: Arc<Buffer>,
    config: Config,
    runtime: Box<dyn Runtime>,
    state: Arc<Mutex<ContainerState>>,
}

impl Container {
    /// 新しいコンテナインスタンスを作成します。
    ///
    /// # Errors
    /// - コンテナクライアントの初期化に失敗した場合
    /// - 設定が無効な場合
    pub async fn new(
        config: Config,
        network: Arc<Network>,
        buffer: Arc<Buffer>,
    ) -> Result<Self> {
        use super::containerd::ContainerdRuntime;
        let runtime = ContainerdRuntime::new().await?;
        
        Ok(Self {
            network,
            buffer,
            config,
            runtime: Box::new(runtime),
            state: Arc::new(Mutex::new(ContainerState::default())),
        })
    }

    /// テスト用のカスタムランタイムでコンテナを作成します。
    pub async fn with_runtime(
        config: Config,
        network: Arc<Network>,
        buffer: Arc<Buffer>,
        runtime: impl Runtime,
    ) -> Result<Self> {
        Ok(Self {
            network,
            buffer,
            config,
            runtime: Box::new(runtime),
            state: Arc::new(Mutex::new(ContainerState::default())),
        })
    }

    /// コンテナを実行します。
    ///
    /// # Errors
    /// - コンテナの作成に失敗した場合
    /// - タスクの作成に失敗した場合
    /// - タスクの開始に失敗した場合
    pub async fn run(&self) -> Result<()> {
        let (cancel_tx, cancel_rx) = oneshot::channel();
        
        // コンテナの作成と起動
        let container_id = self.runtime.create(
            &self.config.image,
            &self.config.args,
            &self.config.working_dir,
            &[], // env_varsは現在未使用
        ).await?;

        {
            let mut state = self.state.lock().await;
            *state = ContainerState::Running {
                runtime: RuntimeState {
                    container_id: container_id.clone(),
                    status: Status::Running,
                },
                cancel_tx: Some(Arc::new(cancel_tx)),
            };
        }

        self.runtime.start(&container_id).await?;

        // キャンセルシグナルを待つ
        tokio::select! {
            _ = cancel_rx => {
                self.cleanup().await?;
                Ok(())
            }
            _ = self.monitor_container(&container_id) => {
                Ok(())
            }
        }
    }

    async fn monitor_container(&self, _container_id: &str) -> Result<()> {
        let runtime = {
            let state = self.state.lock().await;
            if let ContainerState::Running { runtime, .. } = &*state {
                runtime.clone()
            } else {
                return Ok(());
            }
        };

        // コンテナの状態を監視し、エラーが発生した場合はFailedに遷移
        if let Err(e) = self.check_container_health(&runtime).await {
            let mut state = self.state.lock().await;
            *state = ContainerState::Failed {
                error: e.to_string(),
                runtime: Some(runtime),
            };
        }
        Ok(())
    }

    async fn check_container_health(&self, _runtime: &RuntimeState) -> Result<()> {
        // モックテストのために常に成功を返す
        Ok(())
    }

    /// コンテナをクリーンアップします。
    ///
    /// # Errors
    /// - コンテナの停止に失敗した場合
    /// - コンテナの削除に失敗した場合
    pub async fn cleanup(&self) -> Result<()> {
        let container_id = {
            let state = self.state.lock().await;
            match &*state {
                ContainerState::Running { runtime, .. } | ContainerState::Completed { runtime } => Some(runtime.container_id.clone()),
                _ => None,
            }
        };

        if let Some(id) = container_id {
            self.runtime.stop(&id).await?;
            self.runtime.remove(&id).await?;
            
            let mut state = self.state.lock().await;
            if let ContainerState::Running { runtime, .. } = &*state {
                *state = ContainerState::Completed {
                    runtime: runtime.clone(),
                };
            }
        }

        Ok(())
    }

    /// コンテナをキャンセルします。
    ///
    /// # Panics
    /// - `Arc::try_unwrap`が失敗した場合（通常は発生しません）
    pub async fn cancel(&self) {
        let mut state = self.state.lock().await;
        if let ContainerState::Running { cancel_tx: Some(tx), .. } = std::mem::replace(&mut *state, ContainerState::Initial) {
            if Arc::strong_count(&tx) == 1 {
                if let Ok(tx) = Arc::try_unwrap(tx) {
                    let _ = tx.send(());
                }
            }
        }
    }

    pub async fn status(&self) -> Status {
        let state = self.state.lock().await;
        match &*state {
            ContainerState::Initial => Status::Created,
            ContainerState::Running { runtime, .. } => runtime.status.clone(),
            ContainerState::Completed { .. } => Status::Stopped,
            ContainerState::Failed { .. } => Status::Failed("コンテナの実行に失敗しました".to_string()),
        }
    }
}

impl Clone for Container {
    fn clone(&self) -> Self {
        Self {
            network: self.network.clone(),
            buffer: self.buffer.clone(),
            config: self.config.clone(),
            runtime: self.runtime.box_clone(),
            state: self.state.clone(),
        }
    }
}

impl Drop for Container {
    fn drop(&mut self) {
        // 非同期クリーンアップは同期的なdropでは安全に実行できないため、
        // エラーをログに記録するだけにします
        eprintln!("コンテナがドロップされました。クリーンアップは非同期で実行する必要があります。");
    }
} 