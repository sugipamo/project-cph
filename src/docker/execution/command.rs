use std::process::Command;
use std::borrow::Cow;
use std::time::Duration;
use anyhow::{Result, anyhow};
use async_trait::async_trait;
use crate::message::docker;
use crate::docker::config::Config;
use super::Operations;

/// Dockerコマンドの実行結果を表す構造体
#[derive(Debug)]
pub struct ExecutionResult {
    pub stdout: String,
    pub stderr: String,
    pub exit_code: i32,
}

/// Dockerコマンドの実行を担当する構造体
///
/// # Fields
/// * `name` - 実行するDockerコマンド名
/// * `args` - コマンドの引数リスト
/// * `capture_stderr` - 標準エラー出力をキャプチャするかどうか
#[derive(Clone)]
pub struct Executor {
    name: String,
    args: Vec<String>,
    capture_stderr: bool,
    container_id: Option<String>,
}

impl Executor {
    /// 新しいExecutorインスタンスを作成します
    ///
    /// # Returns
    /// * `Self` - 新しいExecutorインスタンス
    #[must_use = "この関数は新しいExecutorインスタンスを返します"]
    pub fn new(name: impl Into<String>) -> Self {
        Self {
            name: name.into(),
            args: Vec::new(),
            capture_stderr: false,
            container_id: None,
        }
    }

    /// 標準エラー出力のキャプチャを設定します
    ///
    /// # Arguments
    /// * `capture` - キャプチャするかどうか
    ///
    /// # Returns
    /// * `Self` - 新しいExecutorインスタンス
    #[must_use = "この関数は新しいExecutorインスタンスを返します"]
    pub fn capture_stderr(self, capture: bool) -> Self {
        Self {
            capture_stderr: capture,
            ..self
        }
    }

    /// コマンドに単一の引数を追加します
    ///
    /// # Arguments
    /// * `arg` - 追加する引数
    ///
    /// # Returns
    /// * `Self` - 新しいExecutorインスタンス
    #[must_use = "この関数は新しいExecutorインスタンスを返します"]
    pub fn arg<'a, S: Into<Cow<'a, str>>>(self, arg: S) -> Self {
        let mut args = self.args;
        args.push(arg.into().into_owned());
        Self {
            name: self.name,
            args,
            capture_stderr: self.capture_stderr,
            container_id: self.container_id,
        }
    }

    /// コマンドに複数の引数を追加します
    ///
    /// # Arguments
    /// * `args` - 追加する引数のイテレータ
    ///
    /// # Returns
    /// * `Self` - 新しいExecutorインスタンス
    #[must_use = "この関数は新しいExecutorインスタンスを返します"]
    pub fn args<I, S>(self, args: I) -> Self
    where
        I: IntoIterator<Item = S>,
        S: AsRef<str>,
    {
        let mut new_args = self.args;
        new_args.extend(args.into_iter().map(|s| s.as_ref().to_owned()));
        Self {
            name: self.name,
            args: new_args,
            capture_stderr: self.capture_stderr,
            container_id: self.container_id,
        }
    }
}

#[async_trait]
impl Operations for Executor {
    async fn initialize(&mut self, config: Config) -> Result<()> {
        if self.container_id.is_some() {
            return Err(anyhow!(docker::error("container_error", "コンテナは既に初期化されています")));
        }

        let output = Command::new("docker")
            .args(["create", "--rm"])
            .args(["--workdir", config.working_dir.to_str().unwrap_or("/")])
            .args(config.command)
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

    async fn start(&mut self) -> Result<()> {
        let container_id = self.container_id
            .as_ref()
            .ok_or_else(|| anyhow!(docker::error("container_error", "コンテナが初期化されていません")))?;

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

    async fn stop(&mut self) -> Result<()> {
        let container_id = self.container_id
            .as_ref()
            .ok_or_else(|| anyhow!(docker::error("container_error", "コンテナが初期化されていません")))?;

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

    async fn execute(&mut self, command: &str) -> Result<(String, String)> {
        let container_id = self.container_id
            .as_ref()
            .ok_or_else(|| anyhow!(docker::error("container_error", "コンテナが初期化されていません")))?;

        let output = Command::new("docker")
            .args(["exec", container_id])
            .arg(command)
            .output()
            .map_err(|e| anyhow!(docker::error("container_error", e)))?;

        let stdout = String::from_utf8(output.stdout)
            .map_err(|e| anyhow!(docker::error("container_error", format!("標準出力の解析に失敗: {e}"))))?;
        let stderr = String::from_utf8(output.stderr)
            .map_err(|e| anyhow!(docker::error("container_error", format!("標準エラー出力の解析に失敗: {e}"))))?;

        Ok((stdout, stderr))
    }

    async fn write(&mut self, input: &str) -> Result<()> {
        let container_id = self.container_id
            .as_ref()
            .ok_or_else(|| anyhow!(docker::error("container_error", "コンテナが初期化されていません")))?;

        let output = Command::new("docker")
            .args(["exec", "-i", container_id])
            .arg("sh")
            .arg("-c")
            .arg(format!("echo '{input}' > /tmp/input"))
            .output()
            .map_err(|e| anyhow!(docker::error("container_error", e)))?;

        if !output.status.success() {
            let stderr = String::from_utf8_lossy(&output.stderr);
            return Err(anyhow!(docker::error("container_error", stderr)));
        }

        Ok(())
    }

    async fn read_stdout(&mut self, _timeout: Duration) -> Result<String> {
        let container_id = self.container_id
            .as_ref()
            .ok_or_else(|| anyhow!(docker::error("container_error", "コンテナが初期化されていません")))?;

        let output = Command::new("docker")
            .args(["logs", "--tail", "100", container_id])
            .output()
            .map_err(|e| anyhow!(docker::error("container_error", e)))?;

        String::from_utf8(output.stdout)
            .map_err(|e| anyhow!(docker::error("container_error", format!("標準出力の解析に失敗: {e}"))))
    }

    async fn read_stderr(&mut self, _timeout: Duration) -> Result<String> {
        let container_id = self.container_id
            .as_ref()
            .ok_or_else(|| anyhow!(docker::error("container_error", "コンテナが初期化されていません")))?;

        let output = Command::new("docker")
            .args(["logs", "--tail", "100", "--stderr", container_id])
            .output()
            .map_err(|e| anyhow!(docker::error("container_error", e)))?;

        String::from_utf8(output.stderr)
            .map_err(|e| anyhow!(docker::error("container_error", format!("標準エラー出力の解析に失敗: {e}"))))
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[tokio::test]
    async fn test_initialize() {
        let mut executor = Executor::new("test");
        let config = Config {
            working_dir: "/".into(),
            command: vec!["alpine:latest".to_string(), "sh".to_string()],
            env_vars: vec![],
            image: "alpine:latest".to_string(),
        };
        let result = executor.initialize(config).await;
        assert!(result.is_ok());
    }

    #[tokio::test]
    async fn test_execute() {
        let mut executor = Executor::new("test");
        let config = Config {
            working_dir: "/".into(),
            command: vec!["alpine:latest".to_string(), "sh".to_string()],
            env_vars: vec![],
            image: "alpine:latest".to_string(),
        };
        executor.initialize(config).await.unwrap();
        executor.start().await.unwrap();
        let result = executor.execute("echo hello").await;
        assert!(result.is_ok());
    }
} 