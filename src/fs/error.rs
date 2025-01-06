use std::fmt;
use std::io;
use nix::errno::Errno;
use fs_extra::error::Error as FsExtraError;

#[derive(Debug)]
pub enum FsError {
    FileSystem {
        message: String,
        source: Option<io::Error>,
    },
    Backup {
        message: String,
        source: Option<io::Error>,
    },
    Transaction {
        message: String,
        source: Option<Box<dyn std::error::Error>>,
    },
}

impl fmt::Display for FsError {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            FsError::FileSystem { message, source } => {
                write!(f, "ファイルシステムエラー: {}", message)?;
                if let Some(err) = source {
                    write!(f, " (原因: {})", err)?;
                }
                Ok(())
            }
            FsError::Backup { message, source } => {
                write!(f, "バックアップエラー: {}", message)?;
                if let Some(err) = source {
                    write!(f, " (原因: {})", err)?;
                }
                Ok(())
            }
            FsError::Transaction { message, source } => {
                write!(f, "トランザクションエラー: {}", message)?;
                if let Some(err) = source {
                    write!(f, " (原因: {})", err)?;
                }
                Ok(())
            }
        }
    }
}

impl std::error::Error for FsError {
    fn source(&self) -> Option<&(dyn std::error::Error + 'static)> {
        match self {
            FsError::FileSystem { source, .. } => source.as_ref().map(|e| e as _),
            FsError::Backup { source, .. } => source.as_ref().map(|e| e as _),
            FsError::Transaction { source, .. } => source.as_ref().map(|e| &**e as _),
        }
    }
}

impl From<io::Error> for FsError {
    fn from(err: io::Error) -> Self {
        FsError::FileSystem {
            message: err.to_string(),
            source: Some(err),
        }
    }
}

impl From<Errno> for FsError {
    fn from(err: Errno) -> Self {
        FsError::FileSystem {
            message: err.to_string(),
            source: Some(io::Error::from_raw_os_error(err as i32)),
        }
    }
}

impl From<FsExtraError> for FsError {
    fn from(err: FsExtraError) -> Self {
        FsError::FileSystem {
            message: err.to_string(),
            source: Some(io::Error::new(io::ErrorKind::Other, err.to_string())),
        }
    }
}

impl From<String> for FsError {
    fn from(message: String) -> Self {
        FsError::FileSystem {
            message,
            source: None,
        }
    }
}

impl From<&str> for FsError {
    fn from(message: &str) -> Self {
        message.to_string().into()
    }
}

pub type Result<T> = std::result::Result<T, FsError>; 