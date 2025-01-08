pub mod operations;
pub mod path;
pub mod backup;
pub mod manager;
pub mod transaction;

// Re-export commonly used operations
pub use operations::{
    check_exists as exists,
    check_is_file as is_file,
    check_is_directory as is_directory,
    validate::parent_exists as check_permissions,
};

// Re-export path operations
pub use path::{
    Validator as PathValidator,
    ValidationLevel as PathValidationLevel,
    normalize as normalize_path,
    validate as validate_path,
    ensure_path_exists,
};

// Re-export commonly used types and traits
pub use anyhow::{Result, Context};
pub use std::path::{Path, PathBuf};

// Re-export specific types
pub use transaction::{
    FileOperation,
    Transaction,
    State as TransactionState,
    Transition as TransactionTransition,
    CreateFileOperation,
    DeleteFileOperation,
};

pub use backup::Manager as BackupManager;
pub use manager::Manager; 