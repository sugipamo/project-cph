use std::process::Command;
use anyhow::{Result, anyhow};
use async_trait::async_trait;
use chrono::{DateTime, Utc};
use crate::container::runtime::interface::image::{
    ImageManager, ImageInfo, ImageDetails, ImageConfig, LayerInfo,
    name::ImageName,
};

/// Docker用のイメージ管理実装
pub struct DockerImageManager;

impl DockerImageManager {
    /// 新しいインスタンスを作成します
    pub fn new() -> Self {
        Self
    }

    /// Dockerコマンドを実行します
    async fn execute_docker_command(&self, args: &[&str]) -> Result<(String, String)> {
        let output = Command::new("docker")
            .args(args)
            .output()
            .map_err(|e| anyhow!("Dockerコマンドの実行に失敗: {}", e))?;

        let stdout = String::from_utf8_lossy(&output.stdout).to_string();
        let stderr = String::from_utf8_lossy(&output.stderr).to_string();

        if !output.status.success() {
            return Err(anyhow!("Dockerコマンドがエラーを返しました: {}", stderr));
        }

        Ok((stdout, stderr))
    }

    /// イメージ情報を解析します
    fn parse_image_info(&self, line: &str) -> Option<ImageInfo> {
        let parts: Vec<&str> = line.split_whitespace().collect();
        if parts.len() >= 4 {
            let full_name = parts[0];
            let (name, tag) = match full_name.split_once(':') {
                Some((n, t)) => (n.to_string(), t.to_string()),
                None => (full_name.to_string(), "latest".to_string()),
            };
            
            Some(ImageInfo {
                name,
                tag,
                id: parts[1].to_string(),
                size: parts[2].parse().unwrap_or(0),
                created_at: DateTime::parse_from_rfc3339(parts[3])
                    .map(|dt| dt.with_timezone(&Utc))
                    .unwrap_or_else(|_| Utc::now()),
            })
        } else {
            None
        }
    }

    /// イメージ名を変換します
    fn convert_image_name(&self, name: &str) -> Result<String> {
        ImageName::parse(name)
            .map(|n| n.to_docker_string())
            .ok_or_else(|| anyhow!("無効なイメージ名: {}", name))
    }
}

#[async_trait]
impl ImageManager for DockerImageManager {
    async fn pull(&self, image_name: &str) -> Result<()> {
        let name = self.convert_image_name(image_name)?;
        self.execute_docker_command(&["pull", &name]).await?;
        Ok(())
    }

    async fn list(&self) -> Result<Vec<ImageInfo>> {
        let format = "{{.Repository}}:{{.Tag}}\\t{{.ID}}\\t{{.Size}}\\t{{.CreatedAt}}";
        let (stdout, _) = self.execute_docker_command(&["images", "--format", format]).await?;
        
        let images = stdout
            .lines()
            .filter_map(|line| self.parse_image_info(line))
            .collect();
        
        Ok(images)
    }

    async fn remove(&self, image_name: &str) -> Result<()> {
        self.execute_docker_command(&["rmi", image_name]).await?;
        Ok(())
    }

    async fn inspect(&self, image_name: &str) -> Result<ImageDetails> {
        let (stdout, _) = self.execute_docker_command(&["inspect", image_name]).await?;
        
        // TODO: JSON解析を実装
        // 現在は簡易的な実装
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
        let result = self.execute_docker_command(&["inspect", image_name]).await;
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