use crate::error::{CphError, helpers, ErrorExt};
use crate::error::fs::FileSystemErrorKind;

pub fn not_found_err(path: String) -> CphError {
    helpers::fs_error(FileSystemErrorKind::NotFound, "ファイル検索", path)
}

pub fn io_err(error: std::io::Error, context: String) -> CphError {
    helpers::fs_error(FileSystemErrorKind::Io, "ファイル操作", context)
        .with_source(error)
}

pub fn permission_err(path: String) -> CphError {
    helpers::fs_error(FileSystemErrorKind::Permission, "ファイルアクセス", path)
}

pub fn transaction_err(error: std::io::Error, context: String) -> CphError {
    helpers::fs_error(FileSystemErrorKind::Transaction, "トランザクション処理", context)
        .with_source(error)
}

pub fn path_err(path: String) -> CphError {
    helpers::fs_error(FileSystemErrorKind::Path, "パス解決", path)
} 