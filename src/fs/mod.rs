mod backup;
mod docker;
mod error;
mod manager;
mod operations;
mod transaction;

pub use backup::BackupManager;
pub use docker::{copy_to_container, copy_from_container};
pub use error::{io_err, not_found_err, permission_err, transaction_err};
pub use manager::FileManager;
pub use operations::{ensure_directory, ensure_file, read_file, write_file};
pub use transaction::{FileOperation, FileTransaction, CopyOperation, CreateDirectoryOperation}; 