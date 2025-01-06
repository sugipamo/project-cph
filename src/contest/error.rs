use crate::error::{CphError, ContestError, ConfigError, LanguageError};

pub fn site_err(msg: String) -> CphError {
    CphError::Contest(ContestError::Site { message: msg })
}

pub fn language_err(msg: String) -> CphError {
    CphError::Contest(ContestError::Language(LanguageError::Config { message: msg }))
}

pub fn config_err(msg: String) -> CphError {
    CphError::Contest(ContestError::Config(ConfigError::NotFound { path: msg }))
}
