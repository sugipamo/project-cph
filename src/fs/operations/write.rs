use std::path::Path;
use std::fs;
use anyhow::{Result, anyhow};
use crate::message::fs as fs_message;

/// ファイルに文字列を書き込みます
///
/// # Errors
///
/// 以下の場合にエラーを返します：
/// - ファイルの作成に失敗した場合
/// - ファイルの書き込みに失敗した場合
pub fn write_string(path: impl AsRef<Path>, content: &str) -> Result<()> {
    fs::write(path.as_ref(), content)
        .map_err(|e| anyhow!(fs_message::error("write_error", e)))?;
    Ok(())
}

/// ファイルにバイト列を書き込みます
///
/// # Errors
///
/// 以下の場合にエラーを返します：
/// - ファイルの作成に失敗した場合
/// - ファイルの書き込みに失敗した場合
pub fn write_bytes(path: impl AsRef<Path>, content: &[u8]) -> Result<()> {
    fs::write(path.as_ref(), content)
        .map_err(|e| anyhow!(fs_message::error("write_error", e)))?;
    Ok(())
}

/// ファイルに文字列を追記します
///
/// # Errors
///
/// 以下の場合にエラーを返します：
/// - ファイルのオープンに失敗した場合
/// - ファイルの書き込みに失敗した場合
pub fn append_string(path: impl AsRef<Path>, content: &str) -> Result<()> {
    use std::fs::OpenOptions;
    use std::io::Write;

    let mut file = OpenOptions::new()
        .create(true)
        .append(true)
        .open(path)
        .map_err(|e| anyhow!(fs_message::error("write_error", e)))?;

    file.write_all(content.as_bytes())
        .map_err(|e| anyhow!(fs_message::error("write_error", e)))?;

    Ok(())
} 