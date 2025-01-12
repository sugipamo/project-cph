use std::path::Path;
use std::fs;
use anyhow::{Result, anyhow};
use crate::message::fs as fs_message;

/// ファイルの内容を文字列として読み込みます
///
/// # Errors
///
/// 以下の場合にエラーを返します：
/// - ファイルが存在しない場合
/// - ファイルの読み取りに失敗した場合
pub fn read_to_string(path: impl AsRef<Path>) -> Result<String> {
    fs::read_to_string(path.as_ref())
        .map_err(|e| anyhow!(fs_message::error("read_error", e)))
}

/// ファイルの内容をバイト列として読み込みます
///
/// # Errors
///
/// 以下の場合にエラーを返します：
/// - ファイルが存在しない場合
/// - ファイルの読み取りに失敗した場合
pub fn read_bytes(path: impl AsRef<Path>) -> Result<Vec<u8>> {
    fs::read(path.as_ref())
        .map_err(|e| anyhow!(fs_message::error("read_error", e)))
}

/// ファイルのメタデータを取得します
///
/// # Errors
///
/// 以下の場合にエラーを返します：
/// - ファイルが存在しない場合
/// - メタデータの取得に失敗した場合
pub fn get_metadata(path: impl AsRef<Path>) -> Result<fs::Metadata> {
    fs::metadata(path.as_ref())
        .map_err(|e| anyhow!(fs_message::error("metadata_error", e)))
} 