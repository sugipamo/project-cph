use std::process::Output as ProcessOutput;
use anyhow::Result;
use tokio::process::Command;

/// コマンド実行の結果を表す構造体
#[derive(Debug)]
pub struct Output {
    pub status: i32,
    pub stdout: String,
    pub stderr: String,
}

impl From<ProcessOutput> for Output {
    fn from(output: ProcessOutput) -> Self {
        Self {
            status: output.status.code().unwrap_or(-1),
            stdout: String::from_utf8_lossy(&output.stdout).into_owned(),
            stderr: String::from_utf8_lossy(&output.stderr).into_owned(),
        }
    }
}

/// コマンドを実行する
/// 
/// # Arguments
/// 
/// * `command` - 実行するコマンド
/// * `args` - コマンドの引数
/// 
/// # Errors
/// 
/// * コマンドの実行に失敗した場合
pub async fn run(command: &str, args: &[&str]) -> Result<Output> {
    let output = Command::new(command)
        .args(args)
        .output()
        .await?;

    Ok(output.into())
} 