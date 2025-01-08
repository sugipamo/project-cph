pub use anyhow::{Error, Result, Context as _};

// マクロのみを残す
#[macro_export]
macro_rules! create_error {
    ($message:expr) => {
        anyhow::Error::msg($message)
    };
    ($message:expr, $context:expr) => {
        anyhow::Error::msg($message).context($context)
    };
}

// 基本的なエラーマクロ
#[macro_export]
macro_rules! fs_err {
    ($msg:expr) => {
        anyhow::Error::msg($msg).context("ファイルシステムエラー")
    };
    ($fmt:expr, $($arg:tt)*) => {
        anyhow::Error::msg(format!($fmt, $($arg)*)).context("ファイルシステムエラー")
    };
}

#[macro_export]
macro_rules! docker_err {
    ($msg:expr) => {
        anyhow::Error::msg($msg).context("Dockerエラー")
    };
    ($fmt:expr, $($arg:tt)*) => {
        anyhow::Error::msg(format!($fmt, $($arg)*)).context("Dockerエラー")
    };
}

#[macro_export]
macro_rules! config_err {
    ($msg:expr) => {
        anyhow::Error::msg($msg).context("設定エラー")
    };
    ($fmt:expr, $($arg:tt)*) => {
        anyhow::Error::msg(format!($fmt, $($arg)*)).context("設定エラー")
    };
}

#[macro_export]
macro_rules! contest_err {
    ($msg:expr) => {
        anyhow::Error::msg($msg).context("コンテストエラー")
    };
    ($fmt:expr, $($arg:tt)*) => {
        anyhow::Error::msg(format!($fmt, $($arg)*)).context("コンテストエラー")
    };
} 