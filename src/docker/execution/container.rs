use std::path::Path;
use tokio::process::Command;
use crate::error::Result;
use crate::docker::error::container_err;

pub struct ContainerManager {
    container_id: Option<String>,
}

impl ContainerManager {
    pub fn new() -> Self {
        Self {
            container_id: None,
        }
    }

    pub async fn create_container<P: AsRef<Path>>(&mut self, image: &str, cmd: Vec<String>, working_dir: P) -> Result<()> {
        if self.container_id.is_some() {
            return Err(container_err("コンテナは既に作成されています".to_string()));
        }

        let output = Command::new("docker")
            .arg("create")
            .arg("--rm")
            .arg("-w")
            .arg(working_dir.as_ref().to_string_lossy().to_string())
            .arg(image)
            .args(cmd)
            .output()
            .await
            .map_err(|e| container_err(format!("コンテナの作成に失敗しました: {}", e)))?;

        if !output.status.success() {
            let stderr = String::from_utf8_lossy(&output.stderr);
            return Err(container_err(format!("コンテナの作成に失敗しました: {}", stderr)));
        }

        let container_id = String::from_utf8_lossy(&output.stdout)
            .trim()
            .to_string();
        self.container_id = Some(container_id);

        Ok(())
    }

    pub async fn start_container(&self) -> Result<()> {
        let container_id = self.container_id.as_ref()
            .ok_or_else(|| container_err("コンテナが作成されていません".to_string()))?;

        let output = Command::new("docker")
            .arg("start")
            .arg(container_id)
            .output()
            .await
            .map_err(|e| container_err(format!("コンテナの起動に失敗しました: {}", e)))?;

        if !output.status.success() {
            let stderr = String::from_utf8_lossy(&output.stderr);
            return Err(container_err(format!("コンテナの起動に失敗しました: {}", stderr)));
        }

        Ok(())
    }

    pub async fn stop_container(&self) -> Result<()> {
        let container_id = self.container_id.as_ref()
            .ok_or_else(|| container_err("コンテナが作成されていません".to_string()))?;

        let output = Command::new("docker")
            .arg("stop")
            .arg(container_id)
            .output()
            .await
            .map_err(|e| container_err(format!("コンテナの停止に失敗しました: {}", e)))?;

        if !output.status.success() {
            let stderr = String::from_utf8_lossy(&output.stderr);
            return Err(container_err(format!("コンテナの停止に失敗しました: {}", stderr)));
        }

        Ok(())
    }

    pub async fn get_container_id(&self) -> Result<String> {
        self.container_id.clone()
            .ok_or_else(|| container_err("コンテナが作成されていません".to_string()))
    }

    pub async fn get_exit_code(&self) -> Result<i32> {
        let container_id = self.container_id.as_ref()
            .ok_or_else(|| container_err("コンテナが作成されていません".to_string()))?;

        let output = Command::new("docker")
            .arg("inspect")
            .arg(container_id)
            .arg("--format={{.State.ExitCode}}")
            .output()
            .await
            .map_err(|e| container_err(format!("終了コードの取得に失敗しました: {}", e)))?;

        if !output.status.success() {
            let stderr = String::from_utf8_lossy(&output.stderr);
            return Err(container_err(format!("終了コードの取得に失敗しました: {}", stderr)));
        }

        let exit_code = String::from_utf8_lossy(&output.stdout)
            .trim()
            .parse::<i32>()
            .map_err(|e| container_err(format!("終了コードの解析に失敗しました: {}", e)))?;

        Ok(exit_code)
    }

    pub async fn check_image(&self, image: &str) -> Result<bool> {
        let output = Command::new("docker")
            .arg("image")
            .arg("inspect")
            .arg(image)
            .output()
            .await
            .map_err(|e| container_err(format!("イメージの確認に失敗しました: {}", e)))?;

        Ok(output.status.success())
    }

    pub async fn pull_image(&self, image: &str) -> Result<()> {
        let output = Command::new("docker")
            .arg("pull")
            .arg(image)
            .output()
            .await
            .map_err(|e| container_err(format!("イメージの取得に失敗しました: {}", e)))?;

        if !output.status.success() {
            let stderr = String::from_utf8_lossy(&output.stderr);
            return Err(container_err(format!("イメージの取得に失敗しました: {}", stderr)));
        }

        Ok(())
    }
} 