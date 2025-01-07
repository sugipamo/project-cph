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
