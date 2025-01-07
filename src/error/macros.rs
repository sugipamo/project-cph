/// エラーを作成するための共通マクロ
#[macro_export]
macro_rules! create_error {
    // 基本形: メッセージとコンテキスト
    ($message:expr, $context:expr) => {{
        use anyhow::{Error, Context as _};
        Error::msg($message).context($context)
    }};
    // ヒント付き
    ($message:expr, $context:expr, $hint:expr) => {{
        use anyhow::{Error, Context as _};
        use $crate::error::ErrorExt;
        Error::msg($message)
            .context($context)
            .with_hint($hint)
    }};
    // ヒントと重大度付き
    ($message:expr, $context:expr, $hint:expr, $severity:expr) => {{
        use anyhow::{Error, Context as _};
        use $crate::error::ErrorExt;
        Error::msg($message)
            .context($context)
            .with_hint($hint)
            .with_severity($severity)
    }};
}

/// ファイルシステムエラーを作成するマクロ
#[macro_export]
macro_rules! fs_err {
    ($msg:expr) => {
        anyhow::Error::msg($msg).context("ファイルシステムエラー")
    };
    ($fmt:expr, $($arg:tt)*) => {
        anyhow::Error::msg(format!($fmt, $($arg)*)).context("ファイルシステムエラー")
    };
}

/// コンテストエラーを作成するマクロ
#[macro_export]
macro_rules! contest_err {
    ($msg:expr) => {
        anyhow::Error::msg($msg).context("コンテストエラー")
    };
    ($fmt:expr, $($arg:tt)*) => {
        anyhow::Error::msg(format!($fmt, $($arg)*)).context("コンテストエラー")
    };
}

/// 設定エラーを作成するマクロ
#[macro_export]
macro_rules! config_err {
    ($msg:expr) => {
        anyhow::Error::msg($msg).context("設定エラー")
    };
    ($fmt:expr, $($arg:tt)*) => {
        anyhow::Error::msg(format!($fmt, $($arg)*)).context("設定エラー")
    };
}

/// Dockerエラーを作成するマクロ
#[macro_export]
macro_rules! docker_err {
    ($msg:expr) => {
        anyhow::Error::msg($msg).context("Dockerエラー")
    };
    ($fmt:expr, $($arg:tt)*) => {
        anyhow::Error::msg(format!($fmt, $($arg)*)).context("Dockerエラー")
    };
} 