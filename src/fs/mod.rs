pub mod error;
pub mod operations;
pub mod path;
pub mod backup;
pub mod manager;
pub mod transaction;

// Re-export commonly used operations
pub use operations::{
    read_file,
    write_file,
    ensure_directory,
    ensure_file,
    delete_file,
    delete_dir,
    exists,
    is_file,
    is_directory,
    check_permissions,
};

// Re-export path operations
pub use path::{
    PathValidator,
    PathValidationLevel,
    normalize_path,
    validate_path,
    ensure_path_exists,
};

// Re-export commonly used types and traits
pub use anyhow::{Result, Context, Error};
pub use std::path::{Path, PathBuf};

// Re-export specific types
pub use transaction::{
    FileTransaction,
    FileOperation,
    CreateFileOperation,
    DeleteFileOperation,
    TransactionState,
    TransactionTransition,
};

pub use backup::BackupManager;
pub use manager::FileManager; 