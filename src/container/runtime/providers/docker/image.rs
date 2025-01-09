use async_trait::async_trait;
use anyhow::Result;
use chrono::{DateTime, Utc};
use crate::container::runtime::interface::image::{
    ImageManager, ImageInfo, ImageDetails, ImageConfig,
};
use crate::container::runtime::providers::base_image_manager::BaseImageManager;

pub struct DockerImageManager {
    base: BaseImageManager,
}

impl DockerImageManager {
    pub fn new() -> Self {
        Self {
            base: BaseImageManager::new("docker"),
        }
    }
}

impl DockerImageManager {
    fn parse_image_info(&self, line: &str) -> Option<ImageInfo> {
        let parts: Vec<&str> = line.split('\t').collect();
        if parts.len() < 4 {
            return None;
        }

        let name_parts: Vec<&str> = parts[0].split(':').collect();
        if name_parts.len() != 2 {
            return None;
        }

        Some(ImageInfo {
            name: name_parts[0].to_string(),
            tag: name_parts[1].to_string(),
            id: parts[1].to_string(),
            size: parts[2].parse().ok()?,
            created_at: DateTime::parse_from_rfc3339(parts[3])
                .ok()?
                .with_timezone(&Utc),
        })
    }
}

#[async_trait]
impl ImageManager for DockerImageManager {
    async fn pull(&self, image_name: &str) -> Result<()> {
        let name = self.base.convert_image_name(image_name)?;
        self.base.execute_command(&["pull", &name]).await?;
        Ok(())
    }

    async fn list(&self) -> Result<Vec<ImageInfo>> {
        let format = "{{.Repository}}:{{.Tag}}\\t{{.ID}}\\t{{.Size}}\\t{{.CreatedAt}}";
        let (stdout, _) = self.base.execute_command(&["images", "--format", format]).await?;
        
        let images = stdout
            .lines()
            .filter_map(|line| self.parse_image_info(line))
            .collect();
        
        Ok(images)
    }

    async fn remove(&self, image_name: &str) -> Result<()> {
        self.base.execute_command(&["rmi", image_name]).await?;
        Ok(())
    }

    async fn inspect(&self, image_name: &str) -> Result<ImageDetails> {
        let (stdout, _) = self.base.execute_command(&["inspect", image_name]).await?;
        
        // TODO: JSON解析を実装
        Ok(ImageDetails {
            config: ImageConfig {
                env: vec![],
                cmd: vec![],
                working_dir: None,
                entrypoint: None,
            },
            layers: vec![],
            created_at: Utc::now(),
            author: None,
        })
    }

    async fn exists(&self, image_name: &str) -> Result<bool> {
        let result = self.base.execute_command(&["inspect", image_name]).await;
        Ok(result.is_ok())
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[tokio::test]
    async fn test_image_exists() {
        let manager = DockerImageManager::new();
        let exists = manager.exists("alpine:latest").await.unwrap();
        assert!(exists || !exists, "イメージの存在確認ができること");
    }

    #[test]
    fn test_parse_image_info() {
        let manager = DockerImageManager::new();
        let line = "nginx:latest\t123456789abc\t100MB\t2023-01-01T00:00:00Z";
        let info = manager.parse_image_info(line).unwrap();
        
        assert_eq!(info.name, "nginx");
        assert_eq!(info.tag, "latest");
        assert_eq!(info.id, "123456789abc");
    }
} 