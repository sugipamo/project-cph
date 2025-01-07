use anyhow::Error;

pub fn config_err(error: impl Into<String>, message: impl Into<String>) -> Error {
    Error::msg(format!("{}: {}", message.into(), error.into()))
}

pub fn not_found_err(path: impl Into<String>) -> Error {
    Error::msg(format!("設定ファイルが見つかりません: {}", path.into()))
}

pub fn parse_err(error: impl Into<String>) -> Error {
    Error::msg(format!("設定ファイルのパースに失敗しました: {}", error.into()))
}

pub fn validation_err(error: impl Into<String>) -> Error {
    Error::msg(format!("設定値の検証に失敗しました: {}", error.into()))
}

pub fn invalid_value_err(key: impl Into<String>, value: impl Into<String>) -> Error {
    Error::msg(format!("無効な設定値: {} = {}", key.into(), value.into()))
} 