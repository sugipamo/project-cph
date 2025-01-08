use std::path::Path;
use anyhow::{Result, anyhow};
use super::validate::validate_is_file;

/// ファイルの内容を文字列として読み込みます。
/// 
/// # Arguments
/// * `path` - 読み込むファイルのパス
/// 
/// # Errors
/// - パスが存在しない場合
/// - パスがファイルでない場合
/// - ファイルの読み込みに失敗した場合
/// - ファイルの内容がUTF-8でない場合
#[must_use = "この関数はファイルの内容を返します"]
pub fn load_file_as_string(path: impl AsRef<Path>) -> Result<String> {
    let path = path.as_ref();
    validate_is_file(path)?;
    std::fs::read_to_string(path)
        .map_err(|e| anyhow!("ファイルの読み込みに失敗しました: {}", e))
}

/// ファイルの内容をバイト列として読み込みます。
/// 
/// # Arguments
/// * `path` - 読み込むファイルのパス
/// 
/// # Errors
/// - パスが存在しない場合
/// - パスがファイルでない場合
/// - ファイルの読み込みに失敗した場合
#[must_use = "この関数はファイルの内容をバイト列として返します"]
pub fn load_file_as_bytes(path: impl AsRef<Path>) -> Result<Vec<u8>> {
    let path = path.as_ref();
    validate_is_file(path)?;
    std::fs::read(path)
        .map_err(|e| anyhow!("ファイルの読み込みに失敗しました: {}", e))
}

/// ファイルのメタデータを取得します。
/// 
/// # Arguments
/// * `path` - メタデータを取得するファイルのパス
/// 
/// # Errors
/// - パスが存在しない場合
/// - メタデータの取得に失敗した場合
#[must_use = "この関数はファイルのメタデータを返します"]
pub fn get_metadata(path: impl AsRef<Path>) -> Result<std::fs::Metadata> {
    let path = path.as_ref();
    validate_is_file(path)?;
    path.metadata()
        .map_err(|e| anyhow!("メタデータの取得に失敗しました: {}", e))
} 