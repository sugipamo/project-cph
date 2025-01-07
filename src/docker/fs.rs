use std::path::Path;
use std::process::Command;
use anyhow::Result;
use crate::error::fs::io_error as create_io_error;

/// コンテナにファイルをコピーします
pub fn copy_to_container(container_id: &str, source: impl AsRef<Path>, target: impl AsRef<Path>) -> Result<()> {
    // TODO: 実装
    unimplemented!()
}

/// コンテナからファイルをコピーします
pub fn copy_from_container(container_id: &str, source: impl AsRef<Path>, target: impl AsRef<Path>) -> Result<()> {
    // TODO: 実装
    unimplemented!()
} 