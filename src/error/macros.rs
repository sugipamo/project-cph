/// エラーを作成するための共通マクロ
#[macro_export]
macro_rules! create_error {
    // 基本形: 種類、操作、場所
    ($kind:expr, $op:expr, $loc:expr) => {{
        use $crate::error::{CphError, ErrorContext};
        CphError::$kind {
            context: ErrorContext::new($op, $loc),
            kind: $kind,
        }
    }};
    // ヒント付き
    ($kind:expr, $op:expr, $loc:expr, $hint:expr) => {{
        use $crate::error::{CphError, ErrorContext};
        CphError::$kind {
            context: ErrorContext::new($op, $loc).with_hint($hint),
            kind: $kind,
        }
    }};
    // ヒントと重大度付き
    ($kind:expr, $op:expr, $loc:expr, $hint:expr, $severity:expr) => {{
        use $crate::error::{CphError, ErrorContext, ErrorSeverity};
        CphError::$kind {
            context: ErrorContext::new($op, $loc)
                .with_hint($hint)
                .with_severity($severity),
            kind: $kind,
        }
    }};
    // ソース付き
    ($kind:expr, $op:expr, $loc:expr, $hint:expr, $source:expr) => {{
        use $crate::error::{CphError, ErrorContext};
        CphError::$kind {
            context: ErrorContext::new($op, $loc)
                .with_hint($hint)
                .with_source($source),
            kind: $kind,
        }
    }};
    // 全指定
    ($kind:expr, $op:expr, $loc:expr, $hint:expr, $source:expr, $severity:expr) => {{
        use $crate::error::{CphError, ErrorContext, ErrorSeverity};
        CphError::$kind {
            context: ErrorContext::new($op, $loc)
                .with_hint($hint)
                .with_source($source)
                .with_severity($severity),
            kind: $kind,
        }
    }};
}

/// ファイルシステムエラーを作成するマクロ
#[macro_export]
macro_rules! fs_error {
    ($kind:expr, $message:expr) => {
        crate::error::Error::fs($kind, $message)
    };
}

/// コンテストエラーを作成するマクロ
#[macro_export]
macro_rules! contest_error {
    ($op:expr, $loc:expr, $kind:expr) => {
        create_error!(Contest, $op, $loc, $kind)
    };
    ($op:expr, $loc:expr, $kind:expr, $hint:expr) => {
        create_error!(Contest, $op, $loc, $hint, $kind)
    };
    ($op:expr, $loc:expr, $kind:expr, $hint:expr, $source:expr) => {
        create_error!(Contest, $op, $loc, $hint, $source, $kind)
    };
}

/// 設定エラーを作成するマクロ
#[macro_export]
macro_rules! config_error {
    ($kind:expr, $message:expr) => {
        crate::error::Error::config($kind, $message)
    };
}

/// その他のエラーを作成するマクロ
#[macro_export]
macro_rules! other_error {
    ($op:expr, $loc:expr) => {
        create_error!(Other, $op, $loc)
    };
    ($op:expr, $loc:expr, $hint:expr) => {
        create_error!(Other, $op, $loc, $hint)
    };
    ($op:expr, $loc:expr, $hint:expr, $severity:expr) => {
        create_error!(Other, $op, $loc, $hint, $severity)
    };
}

#[macro_export]
macro_rules! docker_error {
    ($kind:expr, $message:expr) => {
        crate::error::Error::docker($kind, $message)
    };
} 