mod kind;
pub mod helpers;

pub use kind::FileSystemErrorKind;
pub use helpers::{
    create_not_found_error,
    create_io_error,
    create_permission_error,
    create_invalid_path_error,
    create_transaction_error,
    create_backup_error,
    create_validation_error,
    create_other_error,
}; 