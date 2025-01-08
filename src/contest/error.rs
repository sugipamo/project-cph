use anyhow::Error;

pub fn command_error(message: impl Into<String>) -> Error {
    Error::msg("コマンドエラー").context(message.into())
}

pub fn empty_command_error() -> Error {
    Error::msg("コマンドが空です")
}

pub fn unknown_command_error(command: impl Into<String>) -> Error {
    Error::msg("未知のコマンド").context(command.into())
}

pub fn unknown_site_error(site: impl Into<String>) -> Error {
    Error::msg("未知のサイト").context(site.into())
}

pub fn site_required_error() -> Error {
    Error::msg("サイトの指定が必要です")
}

pub fn too_many_arguments_error() -> Error {
    Error::msg("引数が多すぎます")
}

pub fn no_contest_selected_error() -> Error {
    Error::msg("コンテストが選択されていません")
}

pub fn unsupported_language_error(language: impl Into<String>) -> Error {
    Error::msg("サポートされていない言語です").context(language.into())
}

pub fn invalid_url_error(url: impl Into<String>) -> Error {
    Error::msg("URLの形式が正しくありません").context(url.into())
}

pub fn parse_error(message: impl Into<String>) -> Error {
    Error::msg("パースに失敗しました").context(message.into())
}

pub fn not_found_error(resource: impl Into<String>) -> Error {
    Error::msg("リソースが見つかりません").context(resource.into())
}

pub fn contest_error(message: impl Into<String>) -> Error {
    Error::msg("コンテストの操作に失敗しました").context(message.into())
}
