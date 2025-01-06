use crate::error::{CphError, ContestError, LanguageError, ConfigError};

pub fn site_err(msg: String) -> CphError {
    CphError::Contest(ContestError::Site {
        message: msg,
        hint: None,
    })
}

pub fn site_err_with_hint(msg: String, hint: String) -> CphError {
    CphError::Contest(ContestError::Site {
        message: msg,
        hint: Some(hint),
    })
}

pub fn language_err(msg: String) -> CphError {
    CphError::Contest(ContestError::Language(LanguageError::Config {
        message: msg,
        help: "言語設定を確認してください。".to_string(),
    }))
}

pub fn config_err(msg: String) -> CphError {
    CphError::Contest(ContestError::Config(ConfigError::InvalidValue {
        field: "contest".to_string(),
        message: msg,
        help: "設定ファイルの内容を確認してください。".to_string(),
    }))
}

pub fn unsupported_language_err(lang: String) -> CphError {
    CphError::Contest(ContestError::Language(LanguageError::Unsupported { lang }))
}

pub fn compiler_not_found_err(compiler: String) -> CphError {
    CphError::Contest(ContestError::Language(LanguageError::CompilerNotFound { compiler }))
}
