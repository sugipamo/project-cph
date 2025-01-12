use std::path::PathBuf;
use anyhow::Result;
use async_trait::async_trait;
use tokio::process::Command;

#[async_trait]
pub trait ImageBuilder: Send + Sync {
    async fn build_image(&self, tag: &str) -> Result<()>;
}

pub struct DockerfileBuilder {
    dockerfile_path: PathBuf,
    context_path: PathBuf,
}

impl DockerfileBuilder {
    /// 新しいDockerfileビルダーを作成します。
    ///
    /// # Arguments
    /// * `dockerfile_path` - Dockerfileのパス
    /// * `context_path` - コンテキストのパス（省略可能）
    ///
    /// # Returns
    /// 新しいDockerfileビルダーのインスタンス
    ///
    /// # Panics
    /// * Dockerfileのパスに親ディレクトリが存在しない場合
    #[must_use]
    pub fn new(dockerfile_path: PathBuf, context_path: Option<PathBuf>) -> Self {
        let context_path = context_path.unwrap_or_else(|| {
            dockerfile_path
                .parent()
                .expect("Dockerfileのパスには親ディレクトリが必要です")
                .to_path_buf()
        });
        Self {
            dockerfile_path,
            context_path,
        }
    }
}

#[async_trait]
impl ImageBuilder for DockerfileBuilder {
    async fn build_image(&self, tag: &str) -> Result<()> {
        let status = Command::new("docker")
            .arg("build")
            .arg("-t")
            .arg(tag)
            .arg("-f")
            .arg(&self.dockerfile_path)
            .arg(&self.context_path)
            .status()
            .await?;

        if !status.success() {
            anyhow::bail!("Failed to build image: {}", status);
        }

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
    /// * `image_type` - イメージの種類
    /// * `source` - ソースの場所
    ///
    /// # Returns
    /// 新しいビルダー設定のインスタンス
    #[must_use]
    pub const fn new(image_type: String, source: String) -> Self {
        Self { image_type, source }
    }

    /// イメージビルダーを作成します。
    ///
    /// # Returns
    /// * `Some(Box<dyn ImageBuilder>)` - イメージビルダーのインスタンス
    /// * `None` - イメージビルダーが不要な場合
    #[must_use]
    pub fn create_builder(&self) -> Option<Box<dyn ImageBuilder>> {
        match self.image_type.as_str() {
            "dockerfile" => Some(Box::new(DockerfileBuilder::new(
                PathBuf::from(&self.source),
                None,
            ))),
            _ => None,
        }
    }
} 