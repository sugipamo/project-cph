use std::sync::Arc;
use tokio::process::Command;
use anyhow::Result;
use crate::container::{
    state::status::ContainerStatus,
    runtime::config::ContainerConfig,
};
use super::events::LifecycleEvent;

pub struct LifecycleManager {
    config: ContainerConfig,
    container_id: Option<String>,
    status: ContainerStatus,
}

impl LifecycleManager {
    pub fn new(config: ContainerConfig) -> Self {
        Self {
            config,
            container_id: None,
            status: ContainerStatus::Created,
        }
    }

    pub async fn handle_event(&mut self, event: LifecycleEvent) -> Result<ContainerStatus> {
        match event {
            LifecycleEvent::Create => self.create().await?,
            LifecycleEvent::Start => self.start().await?,
            LifecycleEvent::Stop => self.stop().await?,
            LifecycleEvent::Remove => self.remove().await?,
        }
        Ok(self.status.clone())
    }

    async fn create(&mut self) -> Result<()> {
        self.status = ContainerStatus::Created;
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
            self.status = ContainerStatus::Failed(String::from_utf8_lossy(&output.stderr).to_string());
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

    async fn start(&mut self) -> Result<()> {
        self.status = ContainerStatus::Starting;
        if let Some(id) = &self.container_id {
            let output = Command::new("docker")
                .args(["start", id])
                .output()
                .await?;

            if !output.status.success() {
                self.status = ContainerStatus::Failed(String::from_utf8_lossy(&output.stderr).to_string());
                return Err(anyhow::anyhow!(
                    "コンテナ起動エラー: {}",
                    String::from_utf8_lossy(&output.stderr)
                ));
            }
            self.status = ContainerStatus::Running;
        }
        Ok(())
    }

    async fn stop(&mut self) -> Result<()> {
        self.status = ContainerStatus::Stopping;
        if let Some(id) = &self.container_id {
            let output = Command::new("docker")
                .args(["stop", id])
                .output()
                .await?;

            if !output.status.success() {
                self.status = ContainerStatus::Failed(String::from_utf8_lossy(&output.stderr).to_string());
                return Err(anyhow::anyhow!(
                    "コンテナ停止エラー: {}",
                    String::from_utf8_lossy(&output.stderr)
                ));
            }
            self.status = ContainerStatus::Stopped;
        }
        Ok(())
    }

    async fn remove(&mut self) -> Result<()> {
        if let Some(id) = self.container_id.take() {
            let output = Command::new("docker")
                .args(["rm", "-f", &id])
                .output()
                .await?;

            if !output.status.success() {
                self.status = ContainerStatus::Failed(String::from_utf8_lossy(&output.stderr).to_string());
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

    pub fn status(&self) -> &ContainerStatus {
        &self.status
    }
} 