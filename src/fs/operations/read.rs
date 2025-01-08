use std::path::Path;
use anyhow::Result;

/// ファイルの内容を文字列として読み込みます
pub fn read_file(path: impl AsRef<Path>) -> Result<String> {
    let path = path.as_ref();
    std::fs::read_to_string(path)
        .map_err(|e| crate::fs::error::io_error(e, path))
}

/// ファイルのメタデータを取得します
pub fn metadata(path: impl AsRef<Path>) -> Result<std::fs::Metadata> {
    let path = path.as_ref();
    std::fs::metadata(path)
        .map_err(|e| crate::fs::error::io_error(e, path))
} 