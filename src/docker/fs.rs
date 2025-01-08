use std::path::Path;
use anyhow::Result;


/// コンテナにファイルをコピーする
pub fn copy_to_container(_container_id: &str, _source: impl AsRef<Path>, _target: impl AsRef<Path>) -> Result<()> {
    // TODO: 実装
    Ok(())
}

/// コンテナからファイルをコピーする
pub fn copy_from_container(_container_id: &str, _source: impl AsRef<Path>, _target: impl AsRef<Path>) -> Result<()> {
    // TODO: 実装
    Ok(())
} 