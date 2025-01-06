use crate::error::CphError;

pub fn site_err(msg: String) -> CphError {
    CphError::Contest(format!("サイトエラー: {}", msg))
}

pub fn language_err(msg: String) -> CphError {
    CphError::Contest(format!("言語エラー: {}", msg))
}

pub fn config_err(msg: String) -> CphError {
    CphError::Contest(format!("設定エラー: {}", msg))
}
