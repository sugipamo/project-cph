use std::path::Path;
use anyhow::Error;

pub fn fs_error(message: impl Into<String>) -> Error {
    Error::msg(message.into())
}

pub fn io_error<P: AsRef<Path>>(error: std::io::Error, path: P) -> Error {
    Error::new(error)
}

pub fn not_found_error<P: AsRef<Path>>(path: P) -> Error {
    Error::msg(format!("ファイルが見つかりません: {}", path.as_ref().display()))
}

pub fn permission_error<P: AsRef<Path>>(path: P) -> Error {
    Error::msg(format!("権限エラー: {}", path.as_ref().display()))
}

pub fn invalid_path_error<P: AsRef<Path>>(path: P) -> Error {
    Error::msg(format!("無効なパス: {}", path.as_ref().display()))
} 