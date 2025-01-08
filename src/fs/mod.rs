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
    verify_basic_permissions as check_permissions,
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