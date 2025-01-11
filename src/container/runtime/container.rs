use std::sync::Arc;
use std::path::PathBuf;
use anyhow::Result;
use tokio::sync::{oneshot, Mutex};
use async_trait::async_trait;
use containerd_client as containerd;
use containerd_client::services::v1::containers_client::ContainersClient;
use containerd_client::services::v1::tasks_client::TasksClient;
use containerd_client::services::v1::Container as ContainerdContainer;
use containerd_client::services::v1::container::{Process, Spec};
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
pub struct Container {
    network: Arc<ContainerNetwork>,
    buffer: Arc<OutputBuffer>,
    cancel_tx: Option<oneshot::Sender<()>>,
    config: ContainerConfig,
    container_id: Option<String>,
    status: ContainerStatus,
    containers_client: ContainersClient<tonic::transport::Channel>,
    tasks_client: TasksClient<tonic::transport::Channel>,
    cleanup_status: Arc<Mutex<bool>>,
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
            cancel_tx: None,
            config,
            container_id: None,
            status: ContainerStatus::Created,
            containers_client,
            tasks_client,
            cleanup_status: Arc::new(Mutex::new(false)),
        })
    }

    pub async fn run(&mut self) -> Result<()> {
        let (cancel_tx, cancel_rx) = oneshot::channel();
        self.cancel_tx = Some(cancel_tx);

        // コンテナの作成と起動
        let container_id = self.create(
            &self.config.image,
            &self.config.command,
            &self.config.working_dir,
            &self.config.env_vars,
        ).await?;

        self.container_id = Some(container_id.clone());
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

    pub async fn cleanup(&mut self) -> Result<()> {
        let mut cleanup_done = self.cleanup_status.lock().await;
        if *cleanup_done {
            return Ok(());
        }

        if let Some(container_id) = &self.container_id {
            self.stop(container_id).await?;
            self.remove(container_id).await?;
        }

        *cleanup_done = true;
        Ok(())
    }

    pub fn cancel(&mut self) {
        if let Some(tx) = self.cancel_tx.take() {
            let _ = tx.send(());
        }
    }
}

impl Drop for Container {
    fn drop(&mut self) {
        // 非同期クリーンアップをブロッキングコンテキストで実行
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
            .create(containerd::with_namespace::default(containerd::services::v1::CreateContainerRequest {
                container: Some(ContainerdContainer {
                    id: container_id.clone(),
                    image: image.to_string(),
                    runtime: Some(containerd::services::v1::container::Runtime {
                        name: "io.containerd.runc.v2".to_string(),
                        options: None,
                    }),
                    spec: Some(Spec {
                        process: Some(Process {
                            args: command.iter().map(|s| s.to_string()).collect(),
                            cwd: working_dir.to_str().unwrap().to_string(),
                            env: env_vars.to_vec(),
                            ..Default::default()
                        }),
                        ..Default::default()
                    }),
                    ..Default::default()
                }),
            }))
            .await?
            .into_inner()
            .container
            .unwrap();

        let task = self
            .tasks_client
            .create(containerd::with_namespace::default(containerd::services::v1::CreateTaskRequest {
                container_id: container.id.clone(),
                ..Default::default()
            }))
            .await?;

        self.tasks_client
            .start(containerd::with_namespace::default(containerd::services::v1::StartRequest {
                container_id: container.id.clone(),
                ..Default::default()
            }))
            .await?;

        Ok(container.id)
    }

    async fn start(&self, container_id: &str) -> Result<()> {
        self.tasks_client
            .create(containerd::with_namespace::default(containerd::services::v1::CreateTaskRequest {
                container_id: container_id.to_string(),
                ..Default::default()
            }))
            .await?;

        self.tasks_client
            .start(containerd::with_namespace::default(containerd::services::v1::StartRequest {
                container_id: container_id.to_string(),
                ..Default::default()
            }))
            .await?;

        Ok(())
    }

    async fn stop(&self, container_id: &str) -> Result<()> {
        self.tasks_client
            .kill(containerd::with_namespace::default(containerd::services::v1::KillRequest {
                container_id: container_id.to_string(),
                signal: 15, // SIGTERM
                ..Default::default()
            }))
            .await?;

        self.tasks_client
            .delete(containerd::with_namespace::default(containerd::services::v1::DeleteTaskRequest {
                container_id: container_id.to_string(),
                ..Default::default()
            }))
            .await?;

        Ok(())
    }

    async fn remove(&self, container_id: &str) -> Result<()> {
        self.containers_client
            .delete(containerd::with_namespace::default(containerd::services::v1::DeleteContainerRequest {
                id: container_id.to_string(),
            }))
            .await?;

        Ok(())
    }
} 