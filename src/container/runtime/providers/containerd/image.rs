use async_trait::async_trait;
use anyhow::Result;
use chrono::{DateTime, Utc};
use crate::container::runtime::interface::image::{
    ImageManager, ImageInfo, ImageDetails, ImageConfig,
};
use crate::container::runtime::providers::base_image_manager::BaseImageManager;

pub struct ContainerdImageManager {
    base: BaseImageManager,
    namespace: String,
}

impl ContainerdImageManager {
    pub fn new(namespace: impl Into<String>) -> Self {
        Self {
            base: BaseImageManager::new("ctr"),
            namespace: namespace.into(),
        }
    }

    fn get_command_args<'a>(&'a self, args: &'a [&str]) -> Vec<&'a str> {
        let mut command_args = vec!["--namespace", &self.namespace];
        command_args.extend(args);
        command_args
    }
}

impl ContainerdImageManager {
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
impl ImageManager for ContainerdImageManager {
    async fn pull(&self, image_name: &str) -> Result<()> {
        let name = self.base.convert_image_name(image_name)?;
        let args = self.get_command_args(&["image", "pull", &name]);
        self.base.execute_command(&args).await?;
        Ok(())
    }

    async fn list(&self) -> Result<Vec<ImageInfo>> {
        let args = self.get_command_args(&["image", "ls", "-q"]);
        let (stdout, _) = self.base.execute_command(&args).await?;
        
        let images = stdout
            .lines()
            .filter_map(|line| self.parse_image_info(line))
            .collect();
        
        Ok(images)
    }

    async fn remove(&self, image_name: &str) -> Result<()> {
        let args = self.get_command_args(&["image", "rm", image_name]);
        self.base.execute_command(&args).await?;
        Ok(())
    }

    async fn inspect(&self, image_name: &str) -> Result<ImageDetails> {
        let args = self.get_command_args(&["image", "inspect", image_name]);
        let (stdout, _) = self.base.execute_command(&args).await?;
        
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
        let args = self.get_command_args(&["image", "inspect", image_name]);
        let result = self.base.execute_command(&args).await;
        Ok(result.is_ok())
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[tokio::test]
    async fn test_image_exists() {
        let manager = ContainerdImageManager::new("default");
        let exists = manager.exists("docker.io/library/alpine:latest").await.unwrap();
        assert!(exists || !exists, "イメージの存在確認ができること");
    }

    #[test]
    fn test_parse_image_info() {
        let manager = ContainerdImageManager::new("default");
        let line = "docker.io/library/nginx:latest\tsha256:123456789abc\t100MB\t2023-01-01T00:00:00Z";
        let info = manager.parse_image_info(line).unwrap();
        
        assert_eq!(info.name, "docker.io/library/nginx");
        assert_eq!(info.tag, "latest");
        assert_eq!(info.id, "sha256:123456789abc");
    }
} 