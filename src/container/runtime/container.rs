use std::sync::Arc;
use std::path::PathBuf;
use anyhow::Result;
use tokio::sync::{oneshot, Mutex};
use async_trait::async_trait;
use containerd_client as containerd;
use containerd_client::services::v1::containers_client::ContainersClient;
use containerd_client::services::v1::tasks_client::TasksClient;
use containerd_client::services::v1::Container as ContainerdContainer;
use prost_types::Any;
use crate::container::{
    state::ContainerStatus,
    communication::ContainerNetwork,
    io::buffer::OutputBuffer,
};
use super::{
    config::ContainerConfig,
    ContainerRuntime,
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
    status: ContainerStatus,
}

#[derive(Clone)]
enum ContainerState {
    Initial,
    Running {
        runtime: RuntimeState,
        cancel_tx: Option<oneshot::Sender<()>>,
    },
    Completed {
        runtime: RuntimeState,
    },
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
    network: Arc<ContainerNetwork>,
    buffer: Arc<OutputBuffer>,
    config: ContainerConfig,
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
        config: ContainerConfig,
        network: Arc<ContainerNetwork>,
        buffer: Arc<OutputBuffer>,
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
            &self.config.command,
            &self.config.working_dir,
            &self.config.env_vars,
        ).await?;

        {
            let mut state = self.state.lock().await;
            *state = ContainerState::Running {
                runtime: RuntimeState {
                    container_id: container_id.clone(),
                    status: ContainerStatus::Running,
                },
                cancel_tx: Some(cancel_tx),
            };
        }

        self.start(&container_id).await?;

        // キャンセルシグナルを待つ
        tokio::select! {
            _ = cancel_rx => {
                self.cleanup().await?;
                Ok(())
            }
            _ = self._monitor_container(&container_id) => {
                Ok(())
            }
        }
    }

    async fn _monitor_container(&self, _container_id: &str) -> Result<()> {
        let mut state = self.state.lock().await;
        match state.deref_mut() {
            ContainerState::Running { runtime, .. } => {
                // コンテナの状態を監視し、エラーが発生した場合はFailedに遷移
                if let Err(e) = self._check_container_health(&runtime).await {
                    *state = ContainerState::Failed {
                        error: e.to_string(),
                        runtime: Some(runtime.clone()),
                    };
                }
            }
            _ => {}
        }
        Ok(())
    }

    async fn _check_container_health(&self, runtime: &RuntimeState) -> Result<()> {
        let client = self.clients.tasks.lock().await;
        let response = client
            .get(containerd::services::v1::GetTaskRequest {
                container_id: runtime.container_id.clone(),
            })
            .await?;
        
        if response.task.is_none() {
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
                ContainerState::Running { runtime, .. } => Some(runtime.container_id.clone()),
                ContainerState::Completed { runtime } => Some(runtime.container_id.clone()),
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

    pub async fn cancel(&self) {
        let mut state = self.state.lock().await;
        if let ContainerState::Running { cancel_tx, .. } = std::mem::replace(&mut *state, ContainerState::Initial) {
            let _ = cancel_tx.send(());
        }
    }

    pub async fn status(&self) -> ContainerStatus {
        let state = self.state.lock().await;
        match &*state {
            ContainerState::Initial => ContainerStatus::Created,
            ContainerState::Running { runtime, .. } => runtime.status.clone(),
            ContainerState::Completed { .. } => ContainerStatus::Stopped,
            ContainerState::Failed { .. } => ContainerStatus::Failed("コンテナの実行に失敗しました".to_string()),
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
impl ContainerRuntime for Container {
    async fn create(
        &self,
        image: &str,
        command: &[String],
        working_dir: &PathBuf,
        env_vars: &[String],
    ) -> Result<String> {
        let container_id = uuid::Uuid::new_v4().to_string();
        let container = {
            let mut client = self.clients.containers.lock().await;
            client
                .create(containerd::services::v1::CreateContainerRequest {
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
                })
                .await?
                .into_inner()
                .container
                .unwrap()
        };

        {
            let mut client = self.clients.tasks.lock().await;
            client
                .create(containerd::services::v1::CreateTaskRequest {
                    container_id: container.id.clone(),
                    ..Default::default()
                })
                .await?;

            client
                .start(containerd::services::v1::StartRequest {
                    container_id: container.id.clone(),
                    ..Default::default()
                })
                .await?;
        }

        Ok(container.id)
    }

    async fn start(&self, container_id: &str) -> Result<()> {
        {
            let mut client = self.clients.tasks.lock().await;
            let response = client
                .create(containerd::services::v1::CreateTaskRequest {
                    container_id: container_id.to_string(),
                    ..Default::default()
                })
                .await?;
            drop(client); // 早期解放
        }

        {
            let mut client = self.clients.tasks.lock().await;
            client
                .start(containerd::services::v1::StartTaskRequest {
                    container_id: container_id.to_string(),
                    ..Default::default()
                })
                .await?;
            drop(client); // 早期解放
        }
        Ok(())
    }

    async fn stop(&self, container_id: &str) -> Result<()> {
        {
            let mut client = self.clients.tasks.lock().await;
            client
                .kill(containerd::services::v1::KillTaskRequest {
                    container_id: container_id.to_string(),
                    signal: 15, // SIGTERM
                    ..Default::default()
                })
                .await?;
            drop(client); // 早期解放
        }

        {
            let mut client = self.clients.tasks.lock().await;
            client
                .delete(containerd::services::v1::DeleteTaskRequest {
                    container_id: container_id.to_string(),
                    ..Default::default()
                })
                .await?;
            drop(client); // 早期解放
        }
        Ok(())
    }

    async fn remove(&self, container_id: &str) -> Result<()> {
        let mut client = self.clients.containers.lock().await;
        client
            .delete(containerd::services::v1::DeleteContainerRequest {
                id: container_id.to_string(),
            })
            .await?;
        drop(client); // 早期解放
        Ok(())
    }
} 