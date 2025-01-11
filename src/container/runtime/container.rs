use std::sync::Arc;
use std::path::Path;
use anyhow::{Result, anyhow};
use tokio::sync::{oneshot, Mutex};
use async_trait::async_trait;
use containerd_client as containerd;
use containerd_client::services::v1::containers_client::ContainersClient;
use containerd_client::services::v1::tasks_client::TasksClient;
use containerd_client::services::v1::Container as ContainerdContainer;
use prost_types::Any;
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
struct ContainerdClients {
    containers: Arc<Mutex<ContainersClient<tonic::transport::Channel>>>,
    tasks: Arc<Mutex<TasksClient<tonic::transport::Channel>>>,
}

impl ContainerdClients {
    async fn new(addr: &str) -> Result<Self> {
        let channel = containerd::connect(addr).await?;
        Ok(Self {
            containers: Arc::new(Mutex::new(ContainersClient::new(channel.clone()))),
            tasks: Arc::new(Mutex::new(TasksClient::new(channel))),
        })
    }
}

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

#[derive(Clone)]
pub struct Container {
    #[allow(dead_code)]
    network: Arc<Network>,
    #[allow(dead_code)]
    buffer: Arc<Buffer>,
    config: Config,
    clients: ContainerdClients,
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
        let clients = ContainerdClients::new("/run/containerd/containerd.sock").await?;

        Ok(Self {
            network,
            buffer,
            config,
            clients,
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
        let container_id = self.create(
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

        self.start(&container_id).await?;

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

    #[allow(clippy::used_underscore_items)]
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

    #[allow(clippy::used_underscore_items)]
    async fn check_container_health(&self, runtime: &RuntimeState) -> Result<()> {
        let response = self.clients.tasks.lock().await
            .get(containerd::services::v1::GetRequest {
                container_id: runtime.container_id.clone(),
                exec_id: String::new(),
            })
            .await?;
        
        if response.get_ref().process.is_none() {
            return Err(anyhow!("タスクが見つかりません"));
        }
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
            self.stop(&id).await?;
            self.remove(&id).await?;
            
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

impl Drop for Container {
    fn drop(&mut self) {
        if let Ok(rt) = tokio::runtime::Handle::try_current() {
            rt.block_on(async {
                let _ = self.cleanup().await;
            });
        }
    }
}

#[async_trait]
impl Runtime for Container {
    async fn create(
        &self,
        image: &str,
        command: &[String],
        working_dir: &Path,
        env_vars: &[String],
    ) -> Result<String> {
        let container_id = uuid::Uuid::new_v4().to_string();
        let request = containerd::services::v1::CreateContainerRequest {
            container: Some(ContainerdContainer {
                id: container_id.clone(),
                image: image.to_string(),
                runtime: Some(containerd::services::v1::container::Runtime {
                    name: "io.containerd.runc.v2".to_string(),
                    options: None,
                }),
                spec: Some(Any {
                    type_url: "types.containerd.io/opencontainers/runtime-spec/1/Spec".to_string(),
                    value: serde_json::to_vec(&serde_json::json!({
                        "ociVersion": "1.0.2",
                        "process": {
                            "args": command,
                            "cwd": working_dir.to_str().expect("作業ディレクトリのパスが無効です"),
                            "env": env_vars,
                            "terminal": false,
                            "user": {
                                "uid": 0,
                                "gid": 0
                            }
                        },
                        "root": {
                            "path": "rootfs"
                        },
                        "linux": {
                            "namespaces": [
                                { "type": "pid" },
                                { "type": "ipc" },
                                { "type": "uts" },
                                { "type": "mount" },
                                { "type": "network" }
                            ]
                        }
                    }))?,
                }),
                ..Default::default()
            }),
        };

        let container = {
            let mut client = self.clients.containers.lock().await;
            client.create(request).await?
                .into_inner()
                .container
                .ok_or_else(|| anyhow!("コンテナの作成に失敗しました"))?
        };

        Ok(container.id)
    }

    async fn start(&self, container_id: &str) -> Result<()> {
        self.clients.tasks.lock().await
            .start(containerd::services::v1::StartRequest {
                container_id: container_id.to_string(),
                exec_id: String::new(),
            })
            .await?;
        Ok(())
    }

    async fn stop(&self, container_id: &str) -> Result<()> {
        self.clients.tasks.lock().await
            .kill(containerd::services::v1::KillRequest {
                container_id: container_id.to_string(),
                exec_id: String::new(),
                signal: 15, // SIGTERM
                all: false,
            })
            .await?;
        Ok(())
    }

    async fn remove(&self, container_id: &str) -> Result<()> {
        self.clients.containers.lock().await
            .delete(containerd::services::v1::DeleteContainerRequest {
                id: container_id.to_string(),
            })
            .await?;
        Ok(())
    }
} 