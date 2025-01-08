use std::path::Path;
use anyhow::Result;
use crate::fs_err;

/// ファイルの内容を文字列として読み込みます
pub fn read_file(path: impl AsRef<Path>) -> Result<String> {
    let path = path.as_ref();
    std::fs::read_to_string(path)
        .map_err(|e| fs_err!("ファイルの読み込みに失敗: {}: {}", path.display(), e))
}

/// ファイルの内容をバイト列として読み込みます
pub fn read_file_bytes(path: impl AsRef<Path>) -> Result<Vec<u8>> {
    let path = path.as_ref();
    std::fs::read(path)
        .map_err(|e| fs_err!("ファイルの読み込みに失敗: {}: {}", path.display(), e))
}

/// ファイルのメタデータを取得します
pub fn get_metadata(path: impl AsRef<Path>) -> Result<std::fs::Metadata> {
    let path = path.as_ref();
    std::fs::metadata(path)
        .map_err(|e| fs_err!("メタデータの取得に失敗: {}: {}", path.display(), e))
} 