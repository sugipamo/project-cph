use std::process::Command;
use anyhow::{Result, anyhow};

pub struct DockerContainer {
    container_id: Option<String>,
}

impl DockerContainer {
    #[must_use = "この関数は新しいDockerContainerインスタンスを返します"]
    pub fn new() -> Self {
        Self {
            container_id: None,
        }
    }

    #[must_use = "この関数はコンテナの作成結果を返します"]
    pub fn create(&mut self, image: &str) -> Result<()> {
        if self.container_id.is_some() {
            return Err(anyhow!("コンテナエラー: コンテナは既に作成されています"));
        }

        let output = Command::new("docker")
            .args(["create", image])
            .output()
            .map_err(|e| anyhow!("コンテナエラー: コンテナの作成に失敗しました: {}", e))?;

        if !output.status.success() {
            let stderr = String::from_utf8_lossy(&output.stderr);
            return Err(anyhow!("コンテナエラー: コンテナの作成に失敗しました: {}", stderr));
        }

        let container_id = String::from_utf8(output.stdout)
            .map_err(|e| anyhow!("コンテナエラー: コンテナIDの解析に失敗しました: {}", e))?
            .trim()
            .to_string();

        self.container_id = Some(container_id);
        Ok(())
    }

    #[must_use = "この関数はコンテナの起動結果を返します"]
    pub fn start(&mut self) -> Result<()> {
        let _container_id = self.container_id
            .as_ref()
            .ok_or_else(|| anyhow!("コンテナエラー: コンテナが作成されていません"))?;

        let output = Command::new("docker")
            .args(["start", _container_id])
            .output()
            .map_err(|e| anyhow!("コンテナエラー: コンテナの起動に失敗しました: {}", e))?;

        if !output.status.success() {
            let stderr = String::from_utf8_lossy(&output.stderr);
            return Err(anyhow!("コンテナエラー: コンテナの起動に失敗しました: {}", stderr));
        }

        Ok(())
    }

    #[must_use = "この関数はコンテナの停止結果を返します"]
    pub fn stop(&mut self) -> Result<()> {
        let _container_id = self.container_id
            .as_ref()
            .ok_or_else(|| anyhow!("コンテナエラー: コンテナが作成されていません"))?;

        let output = Command::new("docker")
            .args(["stop", _container_id])
            .output()
            .map_err(|e| anyhow!("コンテナエラー: コンテナの停止に失敗しました: {}", e))?;

        if !output.status.success() {
            let stderr = String::from_utf8_lossy(&output.stderr);
            return Err(anyhow!("コンテナエラー: コンテナの停止に失敗しました: {}", stderr));
        }

        Ok(())
    }

    #[must_use = "この関数はコンテナの�了コードを返します"]
    pub fn wait(&mut self) -> Result<i32> {
        let _container_id = self.container_id
            .as_ref()
            .ok_or_else(|| anyhow!("コンテナエラー: コンテナが作成されていません"))?;

        let output = Command::new("docker")
            .args(["wait", _container_id])
            .output()
            .map_err(|e| anyhow!("コンテナエラー: 終了コードの取得に失敗しました: {}", e))?;

        if !output.status.success() {
            let stderr = String::from_utf8_lossy(&output.stderr);
            return Err(anyhow!("コンテナエラー: 終了コードの取得に失敗しました: {}", stderr));
        }

        let exit_code = String::from_utf8(output.stdout)
            .map_err(|e| anyhow!("コンテナエラー: 終了コードの解析に失敗しました: {}", e))?
            .trim()
            .parse()
            .map_err(|e| anyhow!("コンテナエラー: 終了コードの解析に失敗しました: {}", e))?;

        Ok(exit_code)
    }

    #[must_use = "この関数はイメージの確認結果を返します"]
    pub fn ensure_image(&self, image: &str) -> Result<()> {
        let output = Command::new("docker")
            .args(["images", "-q", image])
            .output()
            .map_err(|e| anyhow!("コンテナエラー: イメージの確認に失敗しました: {}", e))?;

        if output.stdout.is_empty() {
            let output = Command::new("docker")
                .args(["pull", image])
                .output()
                .map_err(|e| anyhow!("コンテナエラー: イメージの取得に失敗しました: {}", e))?;

            if !output.status.success() {
                let stderr = String::from_utf8_lossy(&output.stderr);
                return Err(anyhow!("コンテナエラー: イメージの取得に失敗しました: {}", stderr));
            }
        }

        Ok(())
    }
} 