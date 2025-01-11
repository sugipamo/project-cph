use std::sync::Arc;
use std::path::PathBuf;
use anyhow::Result;
use tokio::sync::{oneshot, Mutex};
use async_trait::async_trait;
use containerd_client as containerd;
use containerd_client::services::v1::containers_client::ContainersClient;
use containerd_client::services::v1::tasks_client::TasksClient;
use containerd_client::services::v1::Container as ContainerdContainer;
use tonic::codegen::http::Request;
use tonic::IntoRequest;
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
struct RuntimeState {
    container_id: String,
    status: ContainerStatus,
}

enum ContainerState {
    Initial,
    Running {
        runtime: RuntimeState,
        cancel: oneshot::Sender<()>,
    },
    Completed {
        runtime: RuntimeState,
    },
    Failed {
        runtime: Option<RuntimeState>,
        error: String,
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
    containers_client: ContainersClient<tonic::transport::Channel>,
    tasks_client: TasksClient<tonic::transport::Channel>,
    state: Arc<Mutex<ContainerState>>,
}

impl Container {
    pub async fn new(
        config: ContainerConfig,
        network: Arc<ContainerNetwork>,
        buffer: Arc<OutputBuffer>,
    ) -> Result<Self> {
        let channel = containerd::connect("/run/containerd/containerd.sock").await?;
        let containers_client = ContainersClient::new(channel.clone());
        let tasks_client = TasksClient::new(channel);

        Ok(Self {
            network,
            buffer,
            config,
            containers_client,
            tasks_client,
            state: Arc::new(Mutex::new(ContainerState::default())),
        })
    }

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
                cancel: cancel_tx,
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
        // コンテナの状態を監視し、必要に応じて対応する
        loop {
            tokio::time::sleep(tokio::time::Duration::from_secs(1)).await;
            // 状態チェックなどの実装
        }
    }

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
        if let ContainerState::Running { cancel, .. } = std::mem::replace(&mut *state, ContainerState::Initial) {
            let _ = cancel.send(());
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
        let container = self
            .containers_client
            .create(containerd::services::v1::CreateContainerRequest {
                container: Some(ContainerdContainer {
                    id: container_id.clone(),
                    image: image.to_string(),
                    runtime: Some(containerd::services::v1::container::Runtime {
                        name: "io.containerd.runc.v2".to_string(),
                        options: None,
                    }),
                    spec: Some(containerd::services::v1::Any {
                        type_url: "types.containerd.io/opencontainers/runtime-spec/1/Spec".to_string(),
                        value: serde_json::to_vec(&serde_json::json!({
                            "process": {
                                "args": command,
                                "cwd": working_dir.to_str().unwrap(),
                                "env": env_vars,
                            }
                        }))?,
                    }),
                    ..Default::default()
                }),
            }.into_request())
            .await?
            .into_inner()
            .container
            .unwrap();

        let task = self
            .tasks_client
            .create(containerd::services::v1::CreateTaskRequest {
                container_id: container.id.clone(),
                ..Default::default()
            }.into_request())
            .await?;

        self.tasks_client
            .start(containerd::services::v1::StartRequest {
                container_id: container.id.clone(),
                ..Default::default()
            }.into_request())
            .await?;

        Ok(container.id)
    }

    async fn start(&self, container_id: &str) -> Result<()> {
        self.tasks_client
            .create(containerd::services::v1::CreateTaskRequest {
                container_id: container_id.to_string(),
                ..Default::default()
            }.into_request())
            .await?;

        self.tasks_client
            .start(containerd::services::v1::StartRequest {
                container_id: container_id.to_string(),
                ..Default::default()
            }.into_request())
            .await?;

        Ok(())
    }

    async fn stop(&self, container_id: &str) -> Result<()> {
        self.tasks_client
            .kill(containerd::services::v1::KillRequest {
                container_id: container_id.to_string(),
                signal: 15, // SIGTERM
                ..Default::default()
            }.into_request())
            .await?;

        self.tasks_client
            .delete(containerd::services::v1::DeleteTaskRequest {
                container_id: container_id.to_string(),
                ..Default::default()
            }.into_request())
            .await?;

        Ok(())
    }

    async fn remove(&self, container_id: &str) -> Result<()> {
        self.containers_client
            .delete(containerd::services::v1::DeleteContainerRequest {
                id: container_id.to_string(),
            }.into_request())
            .await?;

        Ok(())
    }
} 