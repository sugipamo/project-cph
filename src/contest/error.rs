use crate::error::{CphError, helpers, ErrorExt};
use crate::error::contest::ContestErrorKind;
use crate::error::config::ConfigErrorKind;

pub fn site_err(msg: String) -> CphError {
    helpers::contest_error(ContestErrorKind::Site, "サイトアクセス", format!("Contest Site: {}", msg))
}

pub fn site_err_with_hint(msg: String, hint: String) -> CphError {
    helpers::contest_error(ContestErrorKind::Site, "サイトアクセス", format!("Contest Site: {}", msg))
        .with_hint(hint)
}

pub fn language_err(msg: String) -> CphError {
    helpers::contest_error(ContestErrorKind::Language, "言語設定", msg)
}

pub fn config_err(msg: String) -> CphError {
    helpers::config_error(ConfigErrorKind::InvalidValue, "コンテスト設定", msg)
}

pub fn unsupported_language_err(lang: String) -> CphError {
    let hint = format!("サポートされていない言語です: {}", lang);
    helpers::contest_error(ContestErrorKind::Language, "言語チェック", lang)
        .with_hint(hint)
}

pub fn compiler_not_found_err(compiler: String) -> CphError {
    let hint = format!("コンパイラが見つかりません: {}", compiler);
    helpers::contest_error(ContestErrorKind::Compiler, "コンパイラチェック", compiler)
        .with_hint(hint)
}

pub fn state_err(msg: String) -> CphError {
    helpers::contest_error(ContestErrorKind::State, "状態管理", msg)
}
