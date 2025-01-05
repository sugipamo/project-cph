mod backup;
mod operations;
mod transaction;
mod manager;

pub use backup::BackupManager;
pub use operations::{CopyOperation, CreateDirOperation, RemoveOperation, FileOperationBuilder};
pub use transaction::{FileTransaction, FileOperation, TransactionState};
pub use manager::FileManager; 