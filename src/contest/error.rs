use crate::error::{CphError, helpers, ErrorExt};

pub fn site_err(msg: String) -> CphError {
    helpers::contest_site(msg)
}

pub fn site_err_with_hint(msg: String, hint: String) -> CphError {
    helpers::contest_site(msg)
        .with_hint(hint)
}

pub fn language_err(msg: String) -> CphError {
    helpers::contest_language(msg)
}

pub fn config_err(msg: String) -> CphError {
    helpers::config_invalid("contest", msg)
}

pub fn unsupported_language_err(lang: String) -> CphError {
    helpers::contest_language(format!("サポートされていない言語です: {}", lang))
}

pub fn compiler_not_found_err(compiler: String) -> CphError {
    helpers::contest_compiler(compiler)
}
