use std::sync::Arc;
use tokio::process::Command;
use anyhow::Result;
use crate::container::state::lifecycle::ContainerStatus;
use super::config::ContainerConfig;

pub struct ContainerLifecycle {
    config: ContainerConfig,
    container_id: Option<String>,
}

impl ContainerLifecycle {
    pub fn new(config: ContainerConfig) -> Self {
        Self {
            config,
            container_id: None,
        }
    }

    pub async fn create(&mut self) -> Result<()> {
        let output = Command::new("docker")
            .args([
                "create",
                "--rm",
                "-w", self.config.working_dir.to_str().unwrap_or("/"),
            ])
            .args(&self.config.env_vars.iter().flat_map(|env| vec!["-e", env]))
            .arg(&self.config.image)
            .args(&self.config.command)
            .output()
            .await?;

        if !output.status.success() {
            return Err(anyhow::anyhow!(
                "コンテナ作成エラー: {}",
                String::from_utf8_lossy(&output.stderr)
            ));
        }

        let container_id = String::from_utf8(output.stdout)?
            .trim()
            .to_string();

        self.container_id = Some(container_id);
        Ok(())
    }

    pub async fn start(&self) -> Result<()> {
        if let Some(id) = &self.container_id {
            let output = Command::new("docker")
                .args(["start", id])
                .output()
                .await?;

            if !output.status.success() {
                return Err(anyhow::anyhow!(
                    "コンテナ起動エラー: {}",
                    String::from_utf8_lossy(&output.stderr)
                ));
            }
        }
        Ok(())
    }

    pub async fn stop(&self) -> Result<()> {
        if let Some(id) = &self.container_id {
            let output = Command::new("docker")
                .args(["stop", id])
                .output()
                .await?;

            if !output.status.success() {
                return Err(anyhow::anyhow!(
                    "コンテナ停止エラー: {}",
                    String::from_utf8_lossy(&output.stderr)
                ));
            }
        }
        Ok(())
    }

    pub async fn remove(&mut self) -> Result<()> {
        if let Some(id) = self.container_id.take() {
            let output = Command::new("docker")
                .args(["rm", "-f", &id])
                .output()
                .await?;

            if !output.status.success() {
                return Err(anyhow::anyhow!(
                    "コンテナ削除エラー: {}",
                    String::from_utf8_lossy(&output.stderr)
                ));
            }
        }
        Ok(())
    }

    pub fn id(&self) -> Option<&str> {
        self.container_id.as_deref()
    }
} 