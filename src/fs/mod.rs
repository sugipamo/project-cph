pub mod backup;
pub mod core;
pub mod manager;
pub mod transaction;

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

pub use crate::error::fs::{
    not_found_error as create_not_found_error,
    io_error as create_io_error,
    permission_error as create_permission_error,
    invalid_path_error as create_invalid_path_error,
    transaction_error as create_transaction_error,
    backup_error as create_backup_error,
    validation_error as create_validation_error,
    fs_error as create_other_error,
}; 