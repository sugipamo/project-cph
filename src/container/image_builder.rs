use std::path::PathBuf;
use anyhow::{Result, anyhow};
use async_trait::async_trait;
use containerd_client as containerd;
use containerd_client::services::v1::images_client::ImagesClient;
use containerd_client::services::v1::content_client::ContentClient;
use std::sync::Arc;
use tokio::sync::Mutex;
use tokio::fs::File;
use tokio::io::AsyncReadExt;

#[async_trait]
pub trait ImageBuilder: Send + Sync {
    async fn build_image(&self, tag: &str) -> Result<()>;
}

pub struct OfficialImageBuilder {
    image_name: String,
    images: Arc<Mutex<ImagesClient<tonic::transport::Channel>>>,
}

impl OfficialImageBuilder {
    /// 新しい公式イメージビルダーを作成します。
    ///
    /// # Arguments
    /// * `image_name` - 公式イメージの名前（例: "python:3.9"）
    /// * `socket_path` - containerdのソケットパス
    ///
    /// # Returns
    /// 新しい公式イメージビルダーのインスタンス
    ///
    /// # Errors
    /// * containerdクライアントの初期化に失敗した場合
    pub async fn new(image_name: String, socket_path: &str) -> Result<Self> {
        let channel = containerd::connect(socket_path).await?;
        Ok(Self {
            image_name,
            images: Arc::new(Mutex::new(ImagesClient::new(channel))),
        })
    }
}

#[async_trait]
impl ImageBuilder for OfficialImageBuilder {
    async fn build_image(&self, tag: &str) -> Result<()> {
        let mut client = self.images.lock().await;
        
        // イメージをプル
        let request = containerd::services::v1::PullImageRequest {
            image: self.image_name.clone(),
            ..Default::default()
        };

        let response = client.pull(request).await?;
        let image = response.into_inner().image
            .ok_or_else(|| anyhow!("Failed to pull image"))?;

        // イメージにタグを付ける
        let request = containerd::services::v1::TagImageRequest {
            name: image.name,
            tag: tag.to_string(),
        };

        client.tag(request).await?;
        Ok(())
    }
}

pub struct TarImageBuilder {
    tar_path: PathBuf,
    images: Arc<Mutex<ImagesClient<tonic::transport::Channel>>>,
    content: Arc<Mutex<ContentClient<tonic::transport::Channel>>>,
}

impl TarImageBuilder {
    /// 新しいtarイメージビルダーを作成します。
    ///
    /// # Arguments
    /// * `tar_path` - イメージのtarファイルのパス
    /// * `socket_path` - containerdのソケットパス
    ///
    /// # Returns
    /// 新しいtarイメージビルダーのインスタンス
    ///
    /// # Errors
    /// * containerdクライアントの初期化に失敗した場合
    pub async fn new(tar_path: PathBuf, socket_path: &str) -> Result<Self> {
        let channel = containerd::connect(socket_path).await?;
        Ok(Self {
            tar_path,
            images: Arc::new(Mutex::new(ImagesClient::new(channel.clone()))),
            content: Arc::new(Mutex::new(ContentClient::new(channel))),
        })
    }
}

#[async_trait]
impl ImageBuilder for TarImageBuilder {
    async fn build_image(&self, tag: &str) -> Result<()> {
        // tarファイルを読み込む
        let mut file = File::open(&self.tar_path).await?;
        let mut contents = Vec::new();
        file.read_to_end(&mut contents).await?;

        let mut content_client = self.content.lock().await;
        let mut images_client = self.images.lock().await;

        // イメージをインポート
        let request = containerd::services::v1::ImportRequest {
            ref_name: tag.to_string(),
            data: contents,
            ..Default::default()
        };

        content_client.import(request).await?;
        Ok(())
    }
}

pub struct BuilderConfig {
    pub image_type: String,
    pub source: String,
}

impl BuilderConfig {
    /// 新しいビルダー設定を作成します。
    ///
    /// # Arguments
    /// * `image_type` - イメージの種類 ("official" または "tar")
    /// * `source` - イメージのソース（公式イメージ名またはtarファイルのパス）
    ///
    /// # Returns
    /// 新しいビルダー設定のインスタンス
    #[must_use]
    pub const fn new(image_type: String, source: String) -> Self {
        Self { image_type, source }
    }

    /// イメージビルダーを作成します。
    ///
    /// # Arguments
    /// * `socket_path` - containerdのソケットパス
    ///
    /// # Returns
    /// * `Some(Box<dyn ImageBuilder>)` - イメージビルダーのインスタンス
    /// * `None` - イメージビルダーが不要な場合
    ///
    /// # Errors
    /// * containerdクライアントの初期化に失敗した場合
    pub async fn create_builder(&self, socket_path: &str) -> Result<Option<Box<dyn ImageBuilder>>> {
        match self.image_type.as_str() {
            "official" => {
                let builder = OfficialImageBuilder::new(self.source.clone(), socket_path).await?;
                Ok(Some(Box::new(builder)))
            },
            "tar" => {
                let builder = TarImageBuilder::new(PathBuf::from(&self.source), socket_path).await?;
                Ok(Some(Box::new(builder)))
            },
            _ => Ok(None),
        }
    }
} 