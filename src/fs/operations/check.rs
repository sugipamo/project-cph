use std::path::Path;
use std::fs::metadata;
use anyhow::{Result, anyhow};

/// パスが存在するかどうかを確認します
#[must_use = "この関数はパスの存在を示すブール値を返します"]
pub fn exists<P: AsRef<Path>>(path: P) -> bool {
    path.as_ref().exists()
}

/// パスがファイルかどうかを確認します
#[must_use = "この関数はパスがファイルであることを示すブール値を返します"]
pub fn is_file<P: AsRef<Path>>(path: P) -> bool {
    path.as_ref().is_file()
}

/// パスがディレクトリかどうかを確認します
#[must_use = "この関数はパスがディレクトリであることを示すブール値を返します"]
pub fn is_directory<P: AsRef<Path>>(path: P) -> bool {
    path.as_ref().is_dir()
}

/// パスの権限を確認します
pub fn check_basic_permissions<P: AsRef<Path>>(path: P, write_required: bool) -> Result<()> {
    let path = path.as_ref();
    let metadata = metadata(path)?;
    
    if !metadata.permissions().readonly() && write_required {
        return Err(anyhow!("アクセス権限がありません: {}", path.display()));
    }
    Ok(())
}

/// パスのパーミッションを確認します。
/// 
/// # Arguments
/// * `path` - 確認するパス
/// * `write_required` - 書き込み権限が必要かどうか
/// 
/// # Errors
/// - パスが存在しない場合
/// - 読み取り権限がない場合
/// - 書き込み権限が必要なのに書き込み権限がない場合
pub fn verify_permissions<P: AsRef<Path>>(path: P, write_required: bool) -> Result<()> {
    let path = path.as_ref();
    if !path.exists() {
        return Err(anyhow!("パスが存在しません: {}", path.display()));
    }

    let metadata = path.metadata()
        .map_err(|e| anyhow!("メタデータの取得に失敗しました: {}", e))?;

    let permissions = metadata.permissions();

    #[cfg(unix)]
    {
        use std::os::unix::fs::PermissionsExt;
        let mode = permissions.mode();
        let can_read = mode & 0o444 != 0;
        let can_write = mode & 0o222 != 0;

        if !can_read {
            return Err(anyhow!("読み取り権限がありません: {}", path.display()));
        }

        if write_required && !can_write {
            return Err(anyhow!("書き込み権限がありません: {}", path.display()));
        }
    }

    Ok(())
} 