use anyhow::{Error, Context as _};
use std::path::Path;

pub fn fs_err(error: impl Into<String>, path: impl AsRef<Path>) -> Error {
    Error::msg(format!("{}: {}", error.into(), path.as_ref().display()))
        .context("ファイルシステムの操作に失敗しました")
}

pub fn not_found_err(path: impl AsRef<Path>) -> Error {
    Error::msg(format!("ファイルが見つかりません: {}", path.as_ref().display()))
        .context("ファイルの存在を確認してください")
}

pub fn permission_err(path: impl AsRef<Path>) -> Error {
    Error::msg(format!("アクセス権限がありません: {}", path.as_ref().display()))
        .context("ファイルのアクセス権限を確認してください")
}

pub fn io_err(error: std::io::Error, path: impl AsRef<Path>) -> Error {
    error.context(format!("I/Oエラー: {}", path.as_ref().display()))
        .context("ファイルシステムの操作に失敗しました")
}

pub fn path_err(error: impl Into<String>, path: impl AsRef<Path>) -> Error {
    Error::msg(format!("パスエラー: {} ({})", error.into(), path.as_ref().display()))
        .context("パスの形式を確認してください")
}

pub fn transaction_err(error: impl Into<String>) -> Error {
    Error::msg(format!("トランザクションエラー: {}", error.into()))
        .context("ファイルシステムのトランザクションに失敗しました")
} 