mod backup;
mod operations;
mod transaction;
mod manager;
mod docker;
mod error;

pub use backup::BackupManager;
pub use operations::{CopyOperation, CreateDirOperation, RemoveOperation, FileOperationBuilder};
pub use transaction::{FileTransaction, FileOperation, TransactionState};
pub use manager::FileManager;
pub use docker::{DockerFileOperations, DefaultDockerFileOperations};
pub use error::{Result, FsError}; 