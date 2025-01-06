use crate::error::{CphError, helpers};

pub fn not_found_err(path: String) -> CphError {
    helpers::fs_not_found("ファイル検索", path)
}

pub fn io_err(error: std::io::Error, context: String) -> CphError {
    helpers::fs_io("ファイル操作", context, error)
}

pub fn permission_err(path: String) -> CphError {
    helpers::fs_permission("ファイルアクセス", path)
}

pub fn transaction_err(error: std::io::Error, context: String) -> CphError {
    helpers::fs_io("トランザクション処理", context, error)
} 