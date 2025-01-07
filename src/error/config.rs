use anyhow::{Error, Context as _};

pub fn config_err(error: impl Into<String>, message: impl Into<String>) -> Error {
    Error::msg(format!("{}: {}", message.into(), error.into()))
        .context("設定の操作に失敗しました")
}

pub fn not_found_err(path: impl Into<String>) -> Error {
    Error::msg(format!("設定ファイルが見つかりません: {}", path.into()))
        .context("設定ファイルの存在を確認してください")
}

pub fn invalid_format_err(message: impl Into<String>) -> Error {
    Error::msg(format!("設定ファイルの形式が不正です: {}", message.into()))
        .context("設定ファイルの形式を確認してください")
}

pub fn invalid_value_err(message: impl Into<String>) -> Error {
    Error::msg(format!("設定値が不正です: {}", message.into()))
        .context("設定値を確認してください")
}

pub fn io_err(error: std::io::Error, message: impl Into<String>) -> Error {
    error.context(message.into())
        .context("設定ファイルのI/O操作に失敗しました")
} 