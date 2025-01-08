use std::process::Command;
use std::borrow::Cow;
use anyhow::{Result, anyhow};

/// Dockerコマンドの実行を担当する構造体
///
/// # Fields
/// * `name` - 実行するDockerコマンド名
/// * `args` - コマンドの引数リスト
#[derive(Clone)]
pub struct Executor {
    name: String,
    args: Vec<String>,
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
        }
    }

    /// コマンドを実行し、結果を返します
    ///
    /// # Returns
    /// * `Result<String>` - コマンドの実行結果
    ///
    /// # Errors
    /// * コマンドの実行に失敗した場合
    /// * 出力の文字列変換に失敗した場合
    #[must_use = "この関数はコマンドの実行結果を返します"]
    pub fn execute(self) -> Result<String> {
        let mut command = Command::new("docker");
        command.arg(&self.name);
        command.args(&self.args);

        let output = command
            .output()
            .map_err(|e| anyhow!("コマンド実行エラー: {}", e))?;

        if !output.status.success() {
            let error = String::from_utf8_lossy(&output.stderr);
            return Err(anyhow!("コマンド実行エラー: コマンドの実行に失敗: {}", error));
        }

        String::from_utf8(output.stdout)
            .map_err(|e| anyhow!("コマンド実行エラー: {}", e))
    }
} 