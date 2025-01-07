pub mod backup;
pub mod core;
pub mod error;
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

pub use error::{
    create_not_found_error,
    create_io_error,
    create_permission_error,
    create_invalid_path_error,
    create_transaction_error,
    create_backup_error,
    create_validation_error,
    create_other_error,
}; 