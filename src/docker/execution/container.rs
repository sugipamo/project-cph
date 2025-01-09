use std::process::Command;
use anyhow::{Result, anyhow};
use async_trait::async_trait;
use crate::message::docker;
use super::RuntimeManager;

/// Dockerコンテナのランタイム管理を担当する構造体
///
/// # Fields
/// * `container_id` - 管理対象のコンテナID（オプション）
/// * `auto_remove` - コンテナを自動的に削除するかどうか
#[derive(Debug)]
pub struct Runtime {
    container_id: Option<String>,
    auto_remove: bool,
}

impl Default for Runtime {
    fn default() -> Self {
        Self::new()
    }
}

impl Runtime {
    /// 新しいRuntimeインスタンスを作成します
    ///
    /// # Returns
    /// * `Self` - 新しいRuntimeインスタンス
    #[must_use = "この関数は新しいRuntimeインスタンスを返します"]
    pub const fn new() -> Self {
        Self {
            container_id: None,
            auto_remove: true,
        }
    }

    /// 自動削除の設定を変更します
    ///
    /// # Arguments
    /// * `auto_remove` - コンテナを自動的に削除するかどうか
    ///
    /// # Returns
    /// * `Self` - 設定を変更したRuntimeインスタンス
    #[must_use = "この関数は新しいRuntimeインスタンスを返します"]
    pub const fn with_auto_remove(mut self, auto_remove: bool) -> Self {
        self.auto_remove = auto_remove;
        self
    }

    /// コンテナを作成します
    ///
    /// # Arguments
    /// * `image` - 使用するDockerイメージ名
    /// * `options` - 追加のDockerオプション
    ///
    /// # Returns
    /// * `Result<()>` - 作成結果
    ///
    /// # Errors
    /// * コンテナが既に作成されている場合
    /// * コンテナの作成に失敗した場合
    pub fn create(&mut self, image: &str, options: &[&str]) -> Result<()> {
        if self.container_id.is_some() {
            return Err(anyhow!(docker::error("container_error", "コンテナは既に作成されています")));
        }

        let mut args = vec!["create"];
        if self.auto_remove {
            args.push("--rm");
        }
        args.extend(options);
        args.push(image);

        let output = Command::new("docker")
            .args(&args)
            .output()
            .map_err(|e| anyhow!(docker::error("container_error", e)))?;

        if !output.status.success() {
            let stderr = String::from_utf8_lossy(&output.stderr);
            return Err(anyhow!(docker::error("container_error", stderr)));
        }

        let container_id = String::from_utf8(output.stdout)
            .map_err(|e| anyhow!(docker::error("container_error", format!("コンテナIDの解析に失敗: {e}"))))?
            .trim()
            .to_string();

        self.container_id = Some(container_id);
        Ok(())
    }

    /// コンテナ内でコマンドを実行します
    ///
    /// # Arguments
    /// * `command` - 実行するコマンドとその引数
    ///
    /// # Returns
    /// * `Result<(String, String)>` - 標準出力と標準エラー出力のタプル
    ///
    /// # Errors
    /// * コンテナが作成されていない場合
    /// * コマンドの実行に失敗した場合
    pub fn execute_command(&self, command: &[&str]) -> Result<(String, String)> {
        let container_id = self.container_id
            .as_ref()
            .ok_or_else(|| anyhow!(docker::error("container_error", "コンテナが作成されていません")))?;

        let mut args = vec!["exec", container_id];
        args.extend(command);

        let output = Command::new("docker")
            .args(&args)
            .output()
            .map_err(|e| anyhow!(docker::error("container_error", e)))?;

        let stdout = String::from_utf8(output.stdout)
            .map_err(|e| anyhow!(docker::error("container_error", format!("標準出力の解析に失敗: {e}"))))?;
        let stderr = String::from_utf8(output.stderr)
            .map_err(|e| anyhow!(docker::error("container_error", format!("標準エラー出力の解析に失敗: {e}"))))?;

        Ok((stdout, stderr))
    }
}

#[async_trait]
impl RuntimeManager for Runtime {
    async fn create_container(&mut self, image: &str, cmd: Vec<String>, working_dir: &str) -> Result<()> {
        if self.container_id.is_some() {
            return Err(anyhow!(docker::error("container_error", "コンテナは既に作成されています")));
        }

        let mut args = vec!["create"];
        if self.auto_remove {
            args.push("--rm");
        }
        args.extend(["-w", working_dir]);
        args.push(image);
        args.extend(cmd.iter().map(String::as_str));

        let output = Command::new("docker")
            .args(&args)
            .output()
            .map_err(|e| anyhow!(docker::error("container_error", e)))?;

        if !output.status.success() {
            let stderr = String::from_utf8_lossy(&output.stderr);
            return Err(anyhow!(docker::error("container_error", stderr)));
        }

        let container_id = String::from_utf8(output.stdout)
            .map_err(|e| anyhow!(docker::error("container_error", format!("コンテナIDの解析に失敗: {e}"))))?
            .trim()
            .to_string();

        self.container_id = Some(container_id);
        Ok(())
    }

    async fn start_container(&mut self) -> Result<()> {
        let container_id = self.container_id
            .as_ref()
            .ok_or_else(|| anyhow!(docker::error("container_error", "コンテナが作成されていません")))?;

        let output = Command::new("docker")
            .args(["start", container_id])
            .output()
            .map_err(|e| anyhow!(docker::error("container_error", e)))?;

        if !output.status.success() {
            let stderr = String::from_utf8_lossy(&output.stderr);
            return Err(anyhow!(docker::error("container_error", stderr)));
        }

        Ok(())
    }

    async fn stop_container(&mut self) -> Result<()> {
        let container_id = self.container_id
            .as_ref()
            .ok_or_else(|| anyhow!(docker::error("container_error", "コンテナが作成されていません")))?;

        let output = Command::new("docker")
            .args(["stop", container_id])
            .output()
            .map_err(|e| anyhow!(docker::error("container_error", e)))?;

        if !output.status.success() {
            let stderr = String::from_utf8_lossy(&output.stderr);
            return Err(anyhow!(docker::error("container_error", stderr)));
        }

        Ok(())
    }

    async fn get_container_id(&self) -> Result<String> {
        self.container_id
            .clone()
            .ok_or_else(|| anyhow!(docker::error("container_error", "コンテナが作成されていません")))
    }

    async fn get_exit_code(&self) -> Result<i32> {
        let container_id = self.container_id
            .as_ref()
            .ok_or_else(|| anyhow!(docker::error("container_error", "コンテナが作成されていません")))?;

        let output = Command::new("docker")
            .args(["wait", container_id])
            .output()
            .map_err(|e| anyhow!(docker::error("container_error", format!("終了コードの取得に失敗: {e}"))))?;

        if !output.status.success() {
            let stderr = String::from_utf8_lossy(&output.stderr);
            return Err(anyhow!(docker::error("container_error", format!("終了コードの取得に失敗: {stderr}"))));
        }

        let exit_code = String::from_utf8(output.stdout)
            .map_err(|e| anyhow!(docker::error("container_error", format!("終了コードの解析に失敗: {e}"))))?
            .trim()
            .parse()
            .map_err(|e| anyhow!(docker::error("container_error", format!("終了コードの解析に失敗: {e}"))))?;

        Ok(exit_code)
    }

    async fn check_image(&self, image: &str) -> Result<bool> {
        let output = Command::new("docker")
            .args(["images", "-q", image])
            .output()
            .map_err(|e| anyhow!(docker::error("container_error", format!("イメージの確認に失敗: {e}"))))?;

        Ok(!output.stdout.is_empty())
    }

    async fn pull_image(&self, image: &str) -> Result<()> {
        let output = Command::new("docker")
            .args(["pull", image])
            .output()
            .map_err(|e| anyhow!(docker::error("container_error", format!("イメージの取得に失敗: {e}"))))?;

        if !output.status.success() {
            let stderr = String::from_utf8_lossy(&output.stderr);
            return Err(anyhow!(docker::error("container_error", format!("イメージの取得に失敗: {stderr}"))));
        }

        Ok(())
    }
}

impl Drop for Runtime {
    fn drop(&mut self) {
        if let Some(container_id) = &self.container_id {
            let _ = Command::new("docker")
                .args(["rm", "-f", container_id])
                .output();
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[tokio::test]
    async fn test_create_container() {
        let mut runtime = Runtime::new();
        let result = runtime.create_container(
            "alpine:latest",
            vec!["sh".to_string()],
            "/",
        ).await;
        assert!(result.is_ok());
        
        if let Ok(container_id) = runtime.get_container_id().await {
            let _ = Command::new("docker")
                .args(["rm", "-f", &container_id])
                .output();
        }
    }

    #[tokio::test]
    async fn test_check_image() {
        let runtime = Runtime::new();
        let result = runtime.check_image("alpine:latest").await;
        assert!(result.is_ok());
    }
} 