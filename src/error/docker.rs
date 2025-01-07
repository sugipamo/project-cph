use anyhow::{Error, Context as _};

pub fn docker_err(error: impl Into<String>, message: impl Into<String>) -> Error {
    Error::msg(format!("{}: {}", message.into(), error.into()))
        .context("Dockerの操作に失敗しました")
}

pub fn execution_err(_: impl Into<String>, message: impl Into<String>) -> Error {
    Error::msg(format!("実行エラー: {}", message.into()))
        .context("Dockerコンテナの実行に失敗しました")
}

pub fn compilation_err(_: impl Into<String>, message: impl Into<String>) -> Error {
    Error::msg(format!("コンパイルエラー: {}", message.into()))
        .context("ソースコードのコンパイルに失敗しました")
}

pub fn container_err(_: impl Into<String>, message: impl Into<String>) -> Error {
    Error::msg(format!("コンテナエラー: {}", message.into()))
        .context("Dockerコンテナが見つかりません")
}

pub fn state_err(_: impl Into<String>, message: impl Into<String>) -> Error {
    Error::msg(format!("状態エラー: {}", message.into()))
        .context("コンテナの状態が不正です")
} 