use anyhow::{Error, Context as _};

pub fn config_err(error: impl Into<String>, message: impl Into<String>) -> Error {
    Error::msg(format!("{}: {}", message.into(), error.into()))
        .context("設定の操作に失敗しました")
}

pub fn not_found_err(path: impl Into<String>) -> Error {
    Error::msg(format!("設定ファイルが見つかりません: {}", path.into()))
        .context("設定ファイルの存在を確認してください")
}

pub fn parse_err(error: impl Into<String>) -> Error {
    Error::msg(format!("設定ファイルのパースに失敗しました: {}", error.into()))
        .context("設定ファイルの形式を確認してください")
}

pub fn validation_err(error: impl Into<String>) -> Error {
    Error::msg(format!("設定値の検証に失敗しました: {}", error.into()))
        .context("設定値を確認してください")
}

pub fn invalid_value_err(key: impl Into<String>, value: impl Into<String>) -> Error {
    Error::msg(format!("無効な設定値: {} = {}", key.into(), value.into()))
        .context("設定値の形式を確認してください")
} 