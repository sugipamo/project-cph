use anyhow::{Error, Context as _};

pub fn contest_error(message: impl Into<String>) -> Error {
    Error::msg(message.into())
        .context("コンテストの操作に失敗しました")
}

pub fn not_found_error(message: impl Into<String>) -> Error {
    Error::msg(message.into())
        .context("リソースが見つかりません")
}

pub fn invalid_language_error(message: impl Into<String>) -> Error {
    Error::msg(message.into())
        .context("サポートされていない言語です")
}

pub fn invalid_url_error(message: impl Into<String>) -> Error {
    Error::msg(message.into())
        .context("URLの形式が正しくありません")
}

pub fn parse_error(message: impl Into<String>) -> Error {
    Error::msg(message.into())
        .context("パースに失敗しました")
}
