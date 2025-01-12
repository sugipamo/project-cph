use std::path::PathBuf;
use anyhow::{Result, anyhow};
use async_trait::async_trait;
use containerd_client as containerd;
use containerd_client::services::v1::images_client::ImagesClient;
use containerd_client::services::v1::containers_client::ContainersClient;
use containerd_client::services::v1::snapshots_client::SnapshotsClient;
use std::sync::Arc;
use tokio::sync::Mutex;
use crate::config;

#[async_trait]
pub trait ImageBuilder: Send + Sync {
    async fn build_image(&self, tag: &str) -> Result<()>;
}

pub struct ContainerdBuilder {
    images: Arc<Mutex<ImagesClient<tonic::transport::Channel>>>,
    containers: Arc<Mutex<ContainersClient<tonic::transport::Channel>>>,
    snapshots: Arc<Mutex<SnapshotsClient<tonic::transport::Channel>>>,
    config: config::Config,
}

impl ContainerdBuilder {
    /// 新しいContainerdビルダーを作成します。
    ///
    /// # Arguments
    /// * `config` - 設定情報
    ///
    /// # Returns
    /// 新しいContainerdビルダーのインスタンス
    ///
    /// # Errors
    /// * containerdへの接続に失敗した場合
    pub async fn new(config: config::Config) -> Result<Self> {
        let socket: String = config.get("system.container.runtime.containerd.socket")?;
        let channel = containerd::connect(&socket).await?;
        Ok(Self {
            images: Arc::new(Mutex::new(ImagesClient::new(channel.clone()))),
            containers: Arc::new(Mutex::new(ContainersClient::new(channel.clone()))),
            snapshots: Arc::new(Mutex::new(SnapshotsClient::new(channel))),
            config,
        })
    }

    /// コンテナからスナップショットを作成します
    async fn create_snapshot_from_container(&self, container_id: &str, snapshot_name: &str) -> Result<()> {
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
}

#[async_trait]
impl ImageBuilder for ContainerdBuilder {
    async fn build_image(&self, tag: &str) -> Result<()> {
        // 1. ベースイメージからコンテナを作成
        let container_id = uuid::Uuid::new_v4().to_string();
        let default_lang: String = self.config.get("languages.default")?;
        let image: String = self.config.get(&format!("languages.{}.container.image", default_lang))?;

        let container = {
            let mut client = self.containers.lock().await;
            client.create(containerd::services::v1::CreateContainerRequest {
                container: Some(containerd::services::v1::Container {
                    id: container_id.clone(),
                    image,
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
            .ok_or_else(|| anyhow!("コンテナの作成に失敗しました"))?
        };

        // 2. セットアップコマンドを実行
        if let Ok(setup_commands) = self.config.get::<Vec<Vec<String>>>(&format!("languages.{}.container.setup", default_lang)) {
            for cmd in setup_commands {
                // TODO: コマンドの実行処理を実装
                // 現在のcontainerdクライアントではexecが直接サポートされていないため
                // 必要に応じてcontainerd-cliやcontainerd-shimを使用する必要があります
            }
        }

        // 3. スナップショットを作成
        let snapshot_name = format!("{}-snapshot", tag);
        self.create_snapshot_from_container(&container.id, &snapshot_name).await?;

        // 4. イメージとして保存
        let mut images = self.images.lock().await;
        images
            .create(containerd::services::v1::CreateImageRequest {
                image: Some(containerd::services::v1::Image {
                    name: tag.to_string(),
                    target: Some(containerd::types::Descriptor {
                        media_type: "application/vnd.oci.image.manifest.v1+json".to_string(),
                        digest: snapshot_name,
                        size: 0,
                        ..Default::default()
                    }),
                    ..Default::default()
                }),
            })
            .await?;

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