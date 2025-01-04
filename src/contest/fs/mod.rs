mod backup;
mod operations;
mod transaction;

pub use backup::BackupManager;
pub use operations::{CopyOperation, CreateDirOperation, RemoveOperation};
pub use transaction::{FileTransaction, FileOperation, TransactionState}; 