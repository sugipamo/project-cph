use std::path::Path;
use anyhow::{Result, anyhow};
use async_trait::async_trait;
use containerd_client as containerd;
use containerd_client::services::v1::containers_client::ContainersClient;
use containerd_client::services::v1::tasks_client::TasksClient;
use containerd_client::services::v1::Container as ContainerdContainer;
use prost_types::Any;
use std::sync::Arc;
use tokio::sync::Mutex;
use super::Runtime;
use super::config;

#[allow(clippy::module_name_repetitions)]
pub struct ContainerdRuntime {
    containers: Arc<Mutex<ContainersClient<tonic::transport::Channel>>>,
    tasks: Arc<Mutex<TasksClient<tonic::transport::Channel>>>,
}

impl ContainerdRuntime {
    /// 新しいランタイムインスタンスを作成します
    ///
    /// # Errors
    /// - コンテナクライアントの初期化に失敗した場合
    pub async fn new() -> Result<Self> {
        let channel = containerd::connect("/run/containerd/containerd.sock").await?;
        Ok(Self {
            containers: Arc::new(Mutex::new(ContainersClient::new(channel.clone()))),
            tasks: Arc::new(Mutex::new(TasksClient::new(channel))),
        })
    }
}

#[async_trait]
impl Runtime for ContainerdRuntime {
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
            let mut client = self.containers.lock().await;
            client.create(request).await?
                .into_inner()
                .container
                .ok_or_else(|| anyhow!("コンテナの作成に失敗しました"))?
        };

        Ok(container.id)
    }

    async fn start(&self, container_id: &str) -> Result<()> {
        self.tasks.lock().await
            .start(containerd::services::v1::StartRequest {
                container_id: container_id.to_string(),
                exec_id: String::new(),
            })
            .await?;
        Ok(())
    }

    async fn stop(&self, container_id: &str) -> Result<()> {
        self.tasks.lock().await
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
        self.containers.lock().await
            .delete(containerd::services::v1::DeleteContainerRequest {
                id: container_id.to_string(),
            })
            .await?;
        Ok(())
    }

    async fn run(&self, config: &config::Config) -> Result<()> {
        let container_id = self.create(
            &config.image,
            &config.args,
            &config.working_dir,
            &[]  // 空の環境変数リスト
        ).await?;
        self.start(&container_id).await?;
        Ok(())
    }

    fn box_clone(&self) -> Box<dyn Runtime> {
        Box::new(Self {
            containers: self.containers.clone(),
            tasks: self.tasks.clone(),
        })
    }
} 