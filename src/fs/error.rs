use crate::error::{CphError, helpers};

pub fn not_found_err(path: String) -> CphError {
    helpers::fs_not_found(path)
}

pub fn io_err(error: std::io::Error, context: String) -> CphError {
    helpers::fs_io(context, error)
}

pub fn permission_err(path: String) -> CphError {
    helpers::fs_permission(path)
}

pub fn transaction_err(error: std::io::Error, context: String) -> CphError {
    helpers::fs_io(context, error)
} 