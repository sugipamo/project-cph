use std::path::{Path, PathBuf};

/// ファイルシステム操作の結果を表す型
pub type Result<T> = anyhow::Result<T>;

/// パスを表す型のエイリアス
pub type FsPath = PathBuf;

/// ファイルの内容を表す型
pub type FileContent = Vec<u8>;

/// ファイルのメタデータを表す型
pub type FileMetadata = std::fs::Metadata;

/// ファイルのパーミッションを表す型
pub type FilePermissions = std::fs::Permissions; 