use thiserror::Error;

#[derive(Debug, Error)]
pub enum ContestError {
    #[error("設定エラー: {0}")]
    Config(String),
    
    #[error("ファイルシステムエラー: {0}")]
    FileSystem(String),
    
    #[error("言語エラー: {0}")]
    Language(String),
    
    #[error("サイトエラー: {0}")]
    Site(String),
}

impl ContestError {
    /// 設定関連のエラーを生成
    pub fn config(message: impl Into<String>) -> Self {
        ContestError::Config(message.into())
    }

    /// ファイルシステム関連のエラーを生成
    pub fn fs(message: impl Into<String>) -> Self {
        ContestError::FileSystem(message.into())
    }

    /// 言語関連のエラーを生成
    pub fn language(message: impl Into<String>) -> Self {
        ContestError::Language(message.into())
    }

    /// サイト関連のエラーを生成
    pub fn site(message: impl Into<String>) -> Self {
        ContestError::Site(message.into())
    }
} 