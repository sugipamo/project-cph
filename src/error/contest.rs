use anyhow::{Error, Context as _};

pub fn contest_err(error: impl Into<String>, message: impl Into<String>) -> Error {
    Error::msg(format!("{}: {}", message.into(), error.into()))
        .context("コンテストの操作に失敗しました")
}

pub fn not_found_err(resource: impl Into<String>) -> Error {
    Error::msg(format!("リソースが見つかりません: {}", resource.into()))
        .context("リソースの存在を確認してください")
}

pub fn invalid_language_err(language: impl Into<String>) -> Error {
    Error::msg(format!("サポートされていない言語です: {}", language.into()))
        .context("対応している言語を確認してください")
}

pub fn invalid_url_err(url: impl Into<String>) -> Error {
    Error::msg(format!("URLの形式が正しくありません: {}", url.into()))
        .context("URLの形式を確認してください")
}

pub fn parse_err(error: impl Into<String>) -> Error {
    Error::msg(format!("パースに失敗しました: {}", error.into()))
        .context("入力データの形式を確認してください")
}

pub fn io_err(error: std::io::Error, message: impl Into<String>) -> Error {
    error.context(message.into())
        .context("I/O操作に失敗しました")
}

pub fn docker_err(error: impl Into<String>) -> Error {
    Error::msg(format!("Dockerの操作に失敗しました: {}", error.into()))
        .context("Dockerの状態を確認してください")
} 