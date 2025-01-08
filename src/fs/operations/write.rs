use std::path::Path;
use anyhow::{Context, Result};

/// ディレクトリが存在することを確認し、存在しない場合は作成します
pub fn ensure_directory(path: impl AsRef<Path>) -> Result<()> {
    std::fs::create_dir_all(path.as_ref())
        .with_context(|| format!("ディレクトリの作成に失敗: {}", path.as_ref().display()))
}

/// ファイルが存在することを確認し、存在しない場合は作成します
pub fn ensure_file(path: impl AsRef<Path>) -> Result<()> {
    let path = path.as_ref();
    if !path.exists() {
        std::fs::write(path, "")
            .with_context(|| format!("ファイルの作成に失敗: {}", path.display()))?;
    }
    Ok(())
}

/// ファイルに内容を書き込みます
pub fn write_file(path: impl AsRef<Path>, content: impl AsRef<[u8]>) -> Result<()> {
    std::fs::write(path.as_ref(), content)
        .with_context(|| format!("ファイルの書き込みに失敗: {}", path.as_ref().display()))
} 