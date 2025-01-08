use std::process::{Command, Output};
use std::borrow::Cow;
use anyhow::{Result, anyhow, Context};
use crate::message::docker;

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
}

impl Executor {
    /// 新しいExecutorインスタンスを作成します
    ///
    /// # Arguments
    /// * `name` - 実行するDockerコマンド名
    ///
    /// # Returns
    /// * `Self` - 新しいExecutorインスタンス
    #[must_use = "この関数は新しいExecutorインスタンスを返します"]
    pub fn new(name: impl Into<String>) -> Self {
        Self {
            name: name.into(),
            args: Vec::new(),
            capture_stderr: false,
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
        }
    }

    /// コマンドを実行し、生の出力を返します
    ///
    /// # Returns
    /// * `Result<Output>` - コマンドの実行結果
    ///
    /// # Errors
    /// * コマンドの実行に失敗した場合
    fn execute_raw(&self) -> Result<Output> {
        Command::new("docker")
            .arg(&self.name)
            .args(&self.args)
            .output()
            .with_context(|| docker::error("command_failed", "コマンドの実行に失敗しました"))
    }

    /// コマンドを実行し、結果を返します
    ///
    /// # Returns
    /// * `Result<ExecutionResult>` - コマンドの実行結果
    ///
    /// # Errors
    /// * コマンドの実行に失敗した場合
    /// * 出力の文字列変換に失敗した場合
    pub fn execute(self) -> Result<ExecutionResult> {
        let output = self.execute_raw()?;

        let stdout = String::from_utf8(output.stdout)
            .with_context(|| docker::error("command_failed", "標準出力の解析に失敗しました"))?;
        let stderr = String::from_utf8(output.stderr)
            .with_context(|| docker::error("command_failed", "標準エラー出力の解析に失敗しました"))?;

        if !output.status.success() {
            if self.capture_stderr {
                return Ok(ExecutionResult {
                    stdout,
                    stderr,
                    exit_code: output.status.code().unwrap_or(-1),
                });
            }
            return Err(anyhow!(docker::error("command_failed", stderr)));
        }

        Ok(ExecutionResult {
            stdout,
            stderr,
            exit_code: 0,
        })
    }

    /// コマンドを実行し、標準出力のみを返します
    ///
    /// # Returns
    /// * `Result<String>` - コマンドの標準出力
    ///
    /// # Errors
    /// * コマンドの実行に失敗した場合
    /// * 出力の文字列変換に失敗した場合
    pub fn execute_output(self) -> Result<String> {
        self.execute().map(|result| result.stdout)
    }
} 