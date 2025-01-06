#[macro_export]
macro_rules! cph_error {
    ($kind:expr, $op:expr, $loc:expr) => {{
        use $crate::error::{CphError, ErrorContext};
        CphError::$kind {
            context: ErrorContext::new($op, $loc),
            kind: $kind,
        }
    }};
    ($kind:expr, $op:expr, $loc:expr, $hint:expr) => {{
        use $crate::error::{CphError, ErrorContext};
        CphError::$kind {
            context: ErrorContext::new($op, $loc).with_hint($hint),
            kind: $kind,
        }
    }};
    ($kind:expr, $op:expr, $loc:expr, $hint:expr, $severity:expr) => {{
        use $crate::error::{CphError, ErrorContext, ErrorSeverity};
        CphError::$kind {
            context: ErrorContext::new($op, $loc)
                .with_hint($hint)
                .with_severity($severity),
            kind: $kind,
        }
    }};
}

#[macro_export]
macro_rules! fs_error {
    ($op:expr, $loc:expr, $kind:expr) => {{
        use $crate::error::{CphError, ErrorContext, fs::FileSystemErrorKind};
        CphError::FileSystem {
            context: ErrorContext::new($op, $loc),
            kind: $kind,
        }
    }};
    ($op:expr, $loc:expr, $kind:expr, $hint:expr) => {{
        use $crate::error::{CphError, ErrorContext, fs::FileSystemErrorKind};
        CphError::FileSystem {
            context: ErrorContext::new($op, $loc).with_hint($hint),
            kind: $kind,
        }
    }};
}

#[macro_export]
macro_rules! docker_error {
    ($op:expr, $loc:expr, $kind:expr) => {{
        use $crate::error::{CphError, ErrorContext, docker::DockerErrorKind};
        CphError::Docker {
            context: ErrorContext::new($op, $loc),
            kind: $kind,
        }
    }};
    ($op:expr, $loc:expr, $kind:expr, $hint:expr) => {{
        use $crate::error::{CphError, ErrorContext, docker::DockerErrorKind};
        CphError::Docker {
            context: ErrorContext::new($op, $loc).with_hint($hint),
            kind: $kind,
        }
    }};
}

#[macro_export]
macro_rules! contest_error {
    ($op:expr, $loc:expr, $kind:expr) => {{
        use $crate::error::{CphError, ErrorContext, contest::ContestErrorKind};
        CphError::Contest {
            context: ErrorContext::new($op, $loc),
            kind: $kind,
        }
    }};
    ($op:expr, $loc:expr, $kind:expr, $hint:expr) => {{
        use $crate::error::{CphError, ErrorContext, contest::ContestErrorKind};
        CphError::Contest {
            context: ErrorContext::new($op, $loc).with_hint($hint),
            kind: $kind,
        }
    }};
}

#[macro_export]
macro_rules! config_error {
    ($op:expr, $loc:expr, $kind:expr) => {{
        use $crate::error::{CphError, ErrorContext, config::ConfigErrorKind};
        CphError::Config {
            context: ErrorContext::new($op, $loc),
            kind: $kind,
        }
    }};
    ($op:expr, $loc:expr, $kind:expr, $hint:expr) => {{
        use $crate::error::{CphError, ErrorContext, config::ConfigErrorKind};
        CphError::Config {
            context: ErrorContext::new($op, $loc).with_hint($hint),
            kind: $kind,
        }
    }};
}

/// エラー変換用のヘルパーマクロ
#[macro_export]
macro_rules! try_with_context {
    ($expr:expr, $op:expr, $loc:expr) => {
        match $expr {
            Ok(val) => Ok(val),
            Err(e) => Err($crate::error::CphError::Other {
                context: $crate::error::ErrorContext::new($op, $loc).with_source(e),
            }),
        }
    };
    ($expr:expr, $op:expr, $loc:expr, $hint:expr) => {
        match $expr {
            Ok(val) => Ok(val),
            Err(e) => Err($crate::error::CphError::Other {
                context: $crate::error::ErrorContext::new($op, $loc)
                    .with_source(e)
                    .with_hint($hint),
            }),
        }
    };
} 