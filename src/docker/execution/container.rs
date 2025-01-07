use std::process::Command;
use crate::docker::error::container_err;
use crate::error::docker::DockerErrorKind;
use crate::error::Result;

pub struct DockerContainer {
    container_id: Option<String>,
}

impl DockerContainer {
    pub fn new() -> Self {
        Self {
            container_id: None,
        }
    }

    pub fn create(&mut self, image: &str) -> Result<()> {
        if self.container_id.is_some() {
            return Err(container_err(
                "コンテナ作成",
                "コンテナは既に作成されています"
            ));
        }

        let output = Command::new("docker")
            .args(["create", image])
            .output()
            .map_err(|e| container_err(
                "コンテナ作成",
                format!("コンテナの作成に失敗しました: {}", e)
            ))?;

        if !output.status.success() {
            let stderr = String::from_utf8_lossy(&output.stderr);
            return Err(container_err(
                "コンテナ作成",
                format!("コンテナの作成に失敗しました: {}", stderr)
            ));
        }

        let container_id = String::from_utf8(output.stdout)
            .map_err(|e| container_err(
                "コンテナ作成",
                format!("コンテナIDの解析に失敗しました: {}", e)
            ))?
            .trim()
            .to_string();

        self.container_id = Some(container_id);
        Ok(())
    }

    pub fn start(&mut self) -> Result<()> {
        let _container_id = self.container_id
            .as_ref()
            .ok_or_else(|| container_err(
                "コンテナ起動",
                "コンテナが作成されていません"
            ))?;

        let output = Command::new("docker")
            .args(["start", _container_id])
            .output()
            .map_err(|e| container_err(
                "コンテナ起動",
                format!("コンテナの起動に失敗しました: {}", e)
            ))?;

        if !output.status.success() {
            let stderr = String::from_utf8_lossy(&output.stderr);
            return Err(container_err(
                "コンテナ起動",
                format!("コンテナの起動に失敗しました: {}", stderr)
            ));
        }

        Ok(())
    }

    pub fn stop(&mut self) -> Result<()> {
        let _container_id = self.container_id
            .as_ref()
            .ok_or_else(|| container_err(
                "コンテナ停止",
                "コンテナが作成されていません"
            ))?;

        let output = Command::new("docker")
            .args(["stop", _container_id])
            .output()
            .map_err(|e| container_err(
                "コンテナ停止",
                format!("コンテナの停止に失敗しました: {}", e)
            ))?;

        if !output.status.success() {
            let stderr = String::from_utf8_lossy(&output.stderr);
            return Err(container_err(
                "コンテナ停止",
                format!("コンテナの停止に失敗しました: {}", stderr)
            ));
        }

        Ok(())
    }

    pub fn wait(&mut self) -> Result<i32> {
        let _container_id = self.container_id
            .as_ref()
            .ok_or_else(|| container_err(
                "コンテナ待機",
                "コンテナが作成されていません"
            ))
            .and_then(|id| Ok(id.clone()))?;

        let _container_id = self.container_id
            .as_ref()
            .ok_or_else(|| container_err(
                "コンテナ待機",
                "コンテナが作成されていません"
            ))?;

        let output = Command::new("docker")
            .args(["wait", _container_id])
            .output()
            .map_err(|e| container_err(
                "コンテナ待機",
                format!("終了コードの取得に失敗しました: {}", e)
            ))?;

        if !output.status.success() {
            let stderr = String::from_utf8_lossy(&output.stderr);
            return Err(container_err(
                "コンテナ待機",
                format!("終了コードの取得に失敗しました: {}", stderr)
            ));
        }

        let exit_code = String::from_utf8(output.stdout)
            .map_err(|e| container_err(
                "コンテナ待機",
                format!("終了コードの解析に失敗しました: {}", e)
            ))?
            .trim()
            .parse()
            .map_err(|e| container_err(
                "コンテナ待機",
                format!("終了コードの解析に失敗しました: {}", e)
            ))?;

        Ok(exit_code)
    }

    pub fn ensure_image(&self, image: &str) -> Result<()> {
        let output = Command::new("docker")
            .args(["images", "-q", image])
            .output()
            .map_err(|e| container_err(
                "イメージ確認",
                format!("イメージの確認に失敗しました: {}", e)
            ))?;

        if output.stdout.is_empty() {
            let output = Command::new("docker")
                .args(["pull", image])
                .output()
                .map_err(|e| container_err(
                    "イメージ取得",
                    format!("イメージの取得に失敗しました: {}", e)
                ))?;

            if !output.status.success() {
                let stderr = String::from_utf8_lossy(&output.stderr);
                return Err(container_err(
                    "イメージ取得",
                    format!("イメージの取得に失敗しました: {}", stderr)
                ));
            }
        }

        Ok(())
    }
} 