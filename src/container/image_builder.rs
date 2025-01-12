use std::path::PathBuf;
use anyhow::{Result, anyhow};
use async_trait::async_trait;
use containerd_client as containerd;
use containerd_client::services::v1::images_client::ImagesClient;
use containerd_client::services::v1::containers_client::ContainersClient;
use containerd_client::services::v1::snapshots_client::SnapshotsClient;
use containerd_client::services::v1::tasks_client::TasksClient;
use std::sync::Arc;
use tokio::sync::Mutex;
use crate::config;
use prost_types::Any;

#[async_trait]
pub trait ImageBuilder: Send + Sync {
    async fn build_image(&self, tag: &str) -> Result<()>;
}

pub struct ContainerdBuilder {
    images: Arc<Mutex<ImagesClient<tonic::transport::Channel>>>,
    containers: Arc<Mutex<ContainersClient<tonic::transport::Channel>>>,
    snapshots: Arc<Mutex<SnapshotsClient<tonic::transport::Channel>>>,
    tasks: Arc<Mutex<TasksClient<tonic::transport::Channel>>>,
    config: config::Config,
}

impl ContainerdBuilder {
    pub async fn new(config: config::Config) -> Result<Self> {
        let socket: String = config.get("system.container.runtime.containerd.socket")?;
        let channel = containerd::connect(&socket).await?;
        Ok(Self {
            images: Arc::new(Mutex::new(ImagesClient::new(channel.clone()))),
            containers: Arc::new(Mutex::new(ContainersClient::new(channel.clone()))),
            snapshots: Arc::new(Mutex::new(SnapshotsClient::new(channel.clone()))),
            tasks: Arc::new(Mutex::new(TasksClient::new(channel))),
            config,
        })
    }

    async fn create_container(&self, image: &str) -> Result<String> {
        let container_id = uuid::Uuid::new_v4().to_string();
        let mut client = self.containers.lock().await;
        let container = client.create(containerd::services::v1::CreateContainerRequest {
            container: Some(containerd::services::v1::Container {
                id: container_id.clone(),
                image: image.to_string(),
                runtime: Some(containerd::services::v1::container::Runtime {
                    name: "io.containerd.runc.v2".to_string(),
                    options: None,
                }),
                ..Default::default()
            }),
        })
        .await?
        .into_inner()
        .container
        .ok_or_else(|| anyhow!("コンテナの作成に失敗しました"))?;

        Ok(container.id)
    }

    async fn start_container(&self, container_id: &str) -> Result<()> {
        let mut tasks = self.tasks.lock().await;
        tasks.create(containerd::services::v1::CreateTaskRequest {
            container_id: container_id.to_string(),
            rootfs: vec![],
            ..Default::default()
        })
        .await?;

        tasks.start(containerd::services::v1::StartTaskRequest {
            container_id: container_id.to_string(),
            ..Default::default()
        })
        .await?;

        Ok(())
    }

    async fn stop_container(&self, container_id: &str) -> Result<()> {
        let mut tasks = self.tasks.lock().await;
        tasks.kill(containerd::services::v1::KillTaskRequest {
            container_id: container_id.to_string(),
            signal: 15, // SIGTERM
            ..Default::default()
        })
        .await?;

        tasks.delete(containerd::services::v1::DeleteTaskRequest {
            container_id: container_id.to_string(),
            ..Default::default()
        })
        .await?;

        Ok(())
    }

    async fn execute_command(&self, container_id: &str, command: &[String]) -> Result<()> {
        let mut tasks = self.tasks.lock().await;
        let exec_id = uuid::Uuid::new_v4().to_string();

        // 環境変数の取得
        let default_lang: String = self.config.get("languages.default")?;
        let env_vars: Vec<String> = self.config.get(&format!("languages.{}.container.env_vars", default_lang))
            .unwrap_or_default();

        // プロセス仕様の作成
        let process_spec = serde_json::json!({
            "terminal": false,
            "args": command,
            "env": env_vars,  // 設定ファイルからの環境変数を使用
            "cwd": "/",
            "capabilities": {
                "bounding": [
                    "CAP_AUDIT_WRITE",
                    "CAP_KILL",
                    "CAP_NET_BIND_SERVICE"
                ],
                "effective": [
                    "CAP_AUDIT_WRITE",
                    "CAP_KILL",
                    "CAP_NET_BIND_SERVICE"
                ],
                "inheritable": [
                    "CAP_AUDIT_WRITE",
                    "CAP_KILL",
                    "CAP_NET_BIND_SERVICE"
                ],
                "permitted": [
                    "CAP_AUDIT_WRITE",
                    "CAP_KILL",
                    "CAP_NET_BIND_SERVICE"
                ],
                "ambient": [
                    "CAP_AUDIT_WRITE",
                    "CAP_KILL",
                    "CAP_NET_BIND_SERVICE"
                ]
            },
            "rlimits": [
                {
                    "type": "RLIMIT_NOFILE",
                    "hard": 1024,
                    "soft": 1024
                }
            ],
            "noNewPrivileges": true
        });

        // Execの作成と実行
        let exec = tasks.exec(containerd::services::v1::ExecProcessRequest {
            container_id: container_id.to_string(),
            exec_id: exec_id.clone(),
            terminal: false,
            stdin: vec![],
            stdout: vec![],
            stderr: vec![],
            spec: Some(Any {
                type_url: "types.containerd.io/opencontainers/runtime-spec/1/Process".to_string(),
                value: serde_json::to_vec(&process_spec)?,
            }),
        })
        .await?;

        // 実行結果の待機
        let status = tasks.wait(containerd::services::v1::WaitTaskRequest {
            container_id: container_id.to_string(),
            exec_id: exec_id.clone(),
        })
        .await?
        .into_inner()
        .exit_status;

        if status != 0 {
            return Err(anyhow!("コマンドの実行に失敗しました: {:?} (exit code: {})", command, status));
        }

        Ok(())
    }

    async fn create_snapshot(&self, container_id: &str, snapshot_name: &str) -> Result<()> {
        let mut snapshots = self.snapshots.lock().await;
        snapshots
            .prepare(containerd::services::v1::PrepareSnapshotRequest {
                snapshotter: "overlayfs".to_string(),
                key: snapshot_name.to_string(),
                parent: container_id.to_string(),
                labels: Default::default(),
            })
            .await?;
        Ok(())
    }

    async fn commit_snapshot(&self, snapshot_name: &str, tag: &str) -> Result<()> {
        let mut images = self.images.lock().await;
        images
            .create(containerd::services::v1::CreateImageRequest {
                image: Some(containerd::services::v1::Image {
                    name: tag.to_string(),
                    labels: {
                        let mut labels = std::collections::HashMap::new();
                        labels.insert("containerd.io/snapshot/overlayfs".to_string(), snapshot_name.to_string());
                        labels
                    },
                    target: Some(containerd::types::Descriptor {
                        media_type: "application/vnd.oci.image.layer.v1.tar+gzip".to_string(),
                        digest: format!("sha256:{}", snapshot_name),
                        size: 0,
                        ..Default::default()
                    }),
                    ..Default::default()
                }),
            })
            .await?;
        Ok(())
    }

    async fn cleanup(&self, container_id: &str) -> Result<()> {
        // コンテナの停止と削除
        self.stop_container(container_id).await?;
        let mut containers = self.containers.lock().await;
        containers
            .delete(containerd::services::v1::DeleteContainerRequest {
                id: container_id.to_string(),
            })
            .await?;
        Ok(())
    }
}

#[async_trait]
impl ImageBuilder for ContainerdBuilder {
    async fn build_image(&self, tag: &str) -> Result<()> {
        // 1. ベースイメージの取得
        let default_lang: String = self.config.get("languages.default")?;
        let image: String = self.config.get(&format!("languages.{}.container.image", default_lang))?;

        // 2. コンテナの作成と起動
        let container_id = self.create_container(&image).await?;
        self.start_container(&container_id).await?;

        // 3. セットアップコマンドの実行
        if let Ok(setup_commands) = self.config.get::<Vec<Vec<String>>>(&format!("languages.{}.container.setup", default_lang)) {
            for cmd in setup_commands {
                self.execute_command(&container_id, &cmd).await?;
            }
        }

        // 4. スナップショットの作成
        let snapshot_name = format!("{}-snapshot", tag);
        self.create_snapshot(&container_id, &snapshot_name).await?;

        // 5. スナップショットからイメージを作成
        self.commit_snapshot(&snapshot_name, tag).await?;

        // 6. クリーンアップ
        self.cleanup(&container_id).await?;

        Ok(())
    }
}

pub struct BuilderConfig {
    pub image_type: String,
    pub source: String,
}

impl BuilderConfig {
    #[must_use]
    pub const fn new(image_type: String, source: String) -> Self {
        Self { image_type, source }
    }

    #[must_use]
    pub async fn create_builder(&self, config: config::Config) -> Option<Box<dyn ImageBuilder>> {
        Some(Box::new(ContainerdBuilder::new(config).await.ok()?))
    }
} 