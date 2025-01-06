use crate::error::{CphError, helpers, ErrorExt};

pub fn site_err(msg: String) -> CphError {
    helpers::contest_site(
        "サイトアクセス",
        "Contest Site",
        Box::new(std::io::Error::new(std::io::ErrorKind::Other, msg))
    )
}

pub fn site_err_with_hint(msg: String, hint: String) -> CphError {
    helpers::contest_site(
        "サイトアクセス",
        "Contest Site",
        Box::new(std::io::Error::new(std::io::ErrorKind::Other, msg))
    ).with_hint(hint)
}

pub fn language_err(msg: String) -> CphError {
    helpers::contest_language("言語設定", msg)
}

pub fn config_err(msg: String) -> CphError {
    helpers::config_invalid("コンテスト設定", "contest", msg)
}

pub fn unsupported_language_err(lang: String) -> CphError {
    let lang_clone = lang.clone();
    helpers::contest_language("言語チェック", lang)
        .with_hint(format!("サポートされていない言語です: {}", lang_clone))
}

pub fn compiler_not_found_err(compiler: String) -> CphError {
    let compiler_clone = compiler.clone();
    helpers::contest_compiler("コンパイラチェック", compiler)
        .with_hint(format!("コンパイラが見つかりません: {}", compiler_clone))
}
