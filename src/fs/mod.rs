pub mod error;
pub mod operations;
pub mod path;
pub mod backup;
pub mod manager;
pub mod transaction;

// Re-export commonly used operations
pub use operations::{
    load_file_as_string as read_file,
    save_to_file as write_file,
    ensure_directory,
    ensure_file,
    remove_file as delete_file,
    remove_dir as delete_dir,
    exists,
    is_file,
    is_directory,
    check_permissions,
};

// Re-export path operations
pub use path::{
    PathValidator,
    ValidationLevel as PathValidationLevel,
    normalize_path,
    validate_path,
    ensure_path_exists,
};

// Re-export commonly used types and traits
pub use anyhow::{Result, Context, Error};
pub use std::path::{Path, PathBuf};

// Re-export specific types
pub use transaction::{
    FileOperation,
    Transaction,
    State as TransactionState,
    Transition as TransactionTransition,
    CreateFileOperation,
    DeleteFileOperation,
    TransactionError,
};

pub use backup::BackupManager;
pub use manager::Manager; 