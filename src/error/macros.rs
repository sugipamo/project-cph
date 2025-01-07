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
macro_rules! fs_error {
    ($message:expr, $context:expr) => {
        create_error!($message, $context)
    };
    ($message:expr, $context:expr, $hint:expr) => {
        create_error!($message, $context, $hint)
    };
}

/// コンテストエラーを作成するマクロ
#[macro_export]
macro_rules! contest_error {
    ($message:expr, $context:expr) => {
        create_error!($message, $context)
    };
    ($message:expr, $context:expr, $hint:expr) => {
        create_error!($message, $context, $hint)
    };
}

/// 設定エラーを作成するマクロ
#[macro_export]
macro_rules! config_error {
    ($message:expr, $context:expr) => {
        create_error!($message, $context)
    };
    ($message:expr, $context:expr, $hint:expr) => {
        create_error!($message, $context, $hint)
    };
}

/// Dockerエラーを作成するマクロ
#[macro_export]
macro_rules! docker_error {
    ($message:expr, $context:expr) => {
        create_error!($message, $context)
    };
    ($message:expr, $context:expr, $hint:expr) => {
        create_error!($message, $context, $hint)
    };
} 