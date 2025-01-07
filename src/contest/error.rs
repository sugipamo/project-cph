use anyhow::Error;

pub fn command_error(message: impl Into<String>) -> Error {
    Error::msg(message.into())
}

pub fn empty_command_error() -> Error {
    command_error("コマンドが空です")
}

pub fn unknown_command_error(command: impl Into<String>) -> Error {
    command_error(format!("未知のコマンド: {}", command.into()))
}

pub fn unknown_site_error(site: impl Into<String>) -> Error {
    command_error(format!("未知のサイト: {}", site.into()))
}

pub fn site_required_error() -> Error {
    command_error("サイトの指定が必要です")
}

pub fn too_many_arguments_error() -> Error {
    command_error("引数が多すぎます")
}

pub fn no_contest_selected_error() -> Error {
    command_error("コンテストが選択されていません")
}

pub fn unsupported_language_error(language: impl Into<String>) -> Error {
    command_error(format!("サポートされていない言語です: {}", language.into()))
}

pub fn invalid_url_error(url: impl Into<String>) -> Error {
    command_error(format!("URLの形式が正しくありません: {}", url.into()))
}

pub fn parse_error(message: impl Into<String>) -> Error {
    command_error(format!("パースに失敗しました: {}", message.into()))
}

pub fn not_found_error(resource: impl Into<String>) -> Error {
    command_error(format!("リソースが見つかりません: {}", resource.into()))
}

pub fn contest_error(message: impl Into<String>) -> Error {
    command_error(format!("コンテストの操作に失敗しました: {}", message.into()))
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_empty_command_error() {
        let error = empty_command_error();
        assert_eq!(error.to_string(), "コマンドが空です");
    }

    #[test]
    fn test_unknown_command_error() {
        let error = unknown_command_error("test");
        assert_eq!(error.to_string(), "未知のコマンド: test");
    }

    #[test]
    fn test_unknown_site_error() {
        let error = unknown_site_error("example");
        assert_eq!(error.to_string(), "未知のサイト: example");
    }

    #[test]
    fn test_site_required_error() {
        let error = site_required_error();
        assert_eq!(error.to_string(), "サイトの指定が必要です");
    }

    #[test]
    fn test_too_many_arguments_error() {
        let error = too_many_arguments_error();
        assert_eq!(error.to_string(), "引数が多すぎます");
    }

    #[test]
    fn test_no_contest_selected_error() {
        let error = no_contest_selected_error();
        assert_eq!(error.to_string(), "コンテストが選択されていません");
    }

    #[test]
    fn test_unsupported_language_error() {
        let error = unsupported_language_error("brainfuck");
        assert_eq!(error.to_string(), "サポートされていない言語です: brainfuck");
    }

    #[test]
    fn test_invalid_url_error() {
        let error = invalid_url_error("not a url");
        assert_eq!(error.to_string(), "URLの形式が正しくありません: not a url");
    }

    #[test]
    fn test_parse_error() {
        let error = parse_error("invalid format");
        assert_eq!(error.to_string(), "パースに失敗しました: invalid format");
    }

    #[test]
    fn test_not_found_error() {
        let error = not_found_error("file.txt");
        assert_eq!(error.to_string(), "リソースが見つかりません: file.txt");
    }

    #[test]
    fn test_contest_error() {
        let error = contest_error("failed to submit");
        assert_eq!(error.to_string(), "コンテストの操作に失敗しました: failed to submit");
    }
}
