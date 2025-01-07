use anyhow::{Error, Context as _};

pub fn contest_error(message: impl Into<String>) -> Error {
    Error::msg(message.into())
        .context("コンテストの操作に失敗しました")
}

pub fn not_found_error(message: impl Into<String>) -> Error {
    Error::msg(message.into())
        .context("リソースが見つかりません")
}

pub fn invalid_language_error(message: impl Into<String>) -> Error {
    Error::msg(message.into())
        .context("サポートされていない言語です")
}

pub fn invalid_url_error(message: impl Into<String>) -> Error {
    Error::msg(message.into())
        .context("URLの形式が正しくありません")
}

pub fn parse_error(message: impl Into<String>) -> Error {
    Error::msg(message.into())
        .context("パースに失敗しました")
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_contest_error() {
        let error = contest_error("テストエラー");
        assert!(error.to_string().contains("テストエラー"));
        assert!(error.to_string().contains("コンテストの操作に失敗しました"));
    }

    #[test]
    fn test_not_found_error() {
        let error = not_found_error("テストリソース");
        assert!(error.to_string().contains("テストリソース"));
        assert!(error.to_string().contains("リソースが見つかりません"));
    }

    #[test]
    fn test_invalid_language_error() {
        let error = invalid_language_error("テスト言語");
        assert!(error.to_string().contains("テスト言語"));
        assert!(error.to_string().contains("サポートされていない言語です"));
    }

    #[test]
    fn test_invalid_url_error() {
        let error = invalid_url_error("テストURL");
        assert!(error.to_string().contains("テストURL"));
        assert!(error.to_string().contains("URLの形式が正しくありません"));
    }

    #[test]
    fn test_parse_error() {
        let error = parse_error("テストパース");
        assert!(error.to_string().contains("テストパース"));
        assert!(error.to_string().contains("パースに失敗しました"));
    }
}
