use std::process::Output;
use tokio::process::Command;
use crate::error::Result;
use crate::docker::error::command_err;

#[derive(Debug)]
pub struct DockerCommand {
    command: String,
    args: Vec<String>,
}

impl DockerCommand {
    pub fn new<S: Into<String>>(command: S) -> Self {
        Self {
            command: command.into(),
            args: Vec::new(),
        }
    }

    pub fn arg<S: Into<String>>(mut self, arg: S) -> Self {
        self.args.push(arg.into());
        self
    }

    pub fn args<I, S>(mut self, args: I) -> Self
    where
        I: IntoIterator<Item = S>,
        S: Into<String>,
    {
        self.args.extend(args.into_iter().map(Into::into));
        self
    }

    pub async fn execute(&self) -> Result<Output> {
        let output = Command::new(&self.command)
            .args(&self.args)
            .output()
            .await
            .map_err(|e| command_err(format!("コマンドの実行に失敗しました: {}", e)))?;

        if !output.status.success() {
            let stderr = String::from_utf8_lossy(&output.stderr);
            return Err(command_err(format!(
                "コマンドが失敗しました: {}",
                stderr
            )));
        }

        Ok(output)
    }
} 