pub mod backup;
pub mod core;
pub mod error;
pub mod manager;
pub mod path;
pub mod transaction;

#[cfg(test)]
pub mod tests;

pub use core::{
    ensure_directory,
    ensure_file,
    read_file,
    write_file,
    delete_file,
    delete_directory,
    exists,
    is_file,
    is_directory,
    metadata,
    check_permissions,
};

pub use path::{
    normalize_path,
    validate_path,
    ensure_path_exists,
};

pub use error::{
    not_found_error,
    io_error,
    permission_error,
    invalid_path_error,
    transaction_error,
    backup_error,
    validation_error,
    ErrorExt,
}; 