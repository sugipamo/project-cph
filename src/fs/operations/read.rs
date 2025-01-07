use crate::fs::error::{not_found_error, invalid_path_error, ErrorExt};
use anyhow::Result;
use std::path::Path;

/// ファイルを読み込みます
pub fn read_file(path: impl AsRef<Path>) -> Result<String> {
    let path = path.as_ref();
    if !path.exists() {
        return Err(not_found_error(path));
    }
    if !path.is_file() {
        return Err(invalid_path_error(path));
    }
    std::fs::read_to_string(path)
        .with_context_io(format!("ファイルの読み込みに失敗: {}", path.display()))
}

/// パスのメタデータを取得します
pub fn get_metadata(path: impl AsRef<Path>) -> Result<std::fs::Metadata> {
    let path = path.as_ref();
    if !path.exists() {
        return Err(not_found_error(path));
    }

    std::fs::metadata(path)
        .with_context_io(format!("メタデータの取得に失敗: {}", path.display()))
} 