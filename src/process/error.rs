use std::path::PathBuf;
use thiserror::Error;

#[derive(Debug, Error)]
pub enum ProcessError {
    #[error("プロセスの起動に失敗しました: {0}")]
    Spawn(String),

    #[error("プロセスがタイムアウトしました（{timeout_secs}秒）")]
    Timeout {
        timeout_secs: u64,
        output: Vec<u8>,
    },

    #[error("メモリ制限（{limit_mb}MB）を超過しました")]
    MemoryLimitExceeded {
        limit_mb: u64,
        usage_mb: u64,
    },

    #[error("プロセスが異常終了しました（終了コード: {code}）")]
    Failure {
        code: i32,
        output: Vec<u8>,
    },

    #[error("プロセスの強制終了に失敗しました: {0}")]
    Kill(String),

    #[error("標準入出力の操作に失敗しました: {0}")]
    Io(String),

    #[error("設定エラー: {0}")]
    Config(String),

    #[error("実行ファイルが見つかりません: {path}")]
    ExecutableNotFound {
        path: PathBuf,
    },

    #[error("プロセスが見つかりません: {id}")]
    ProcessNotFound {
        id: String,
    },

    #[error("バッファ操作に失敗しました: {0}")]
    Buffer(String),

    #[error("その他のエラー: {0}")]
    Other(String),
}

impl From<std::io::Error> for ProcessError {
    fn from(err: std::io::Error) -> Self {
        ProcessError::Io(err.to_string())
    }
}

impl From<anyhow::Error> for ProcessError {
    fn from(err: anyhow::Error) -> Self {
        ProcessError::Other(err.to_string())
    }
} 