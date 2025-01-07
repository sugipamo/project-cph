use anyhow::{Error, Context as _};

pub fn docker_err(error: impl Into<String>, message: impl Into<String>) -> Error {
    Error::msg(format!("{}: {}", message.into(), error.into()))
        .context("Dockerの操作に失敗しました")
}

pub fn container_not_found_err(container_id: impl Into<String>) -> Error {
    Error::msg(format!("コンテナが見つかりません: {}", container_id.into()))
        .context("コンテナの存在を確認してください")
}

pub fn image_not_found_err(image: impl Into<String>) -> Error {
    Error::msg(format!("イメージが見つかりません: {}", image.into()))
        .context("イメージの存在を確認してください")
}

pub fn network_err(error: impl Into<String>) -> Error {
    Error::msg(format!("ネットワークエラー: {}", error.into()))
        .context("ネットワークの接続を確認してください")
}

pub fn execution_err(error: impl Into<String>) -> Error {
    Error::msg(format!("実行エラー: {}", error.into()))
        .context("コマンドの実行に失敗しました")
}

pub fn compilation_err(error: impl Into<String>) -> Error {
    Error::msg(format!("コンパイルエラー: {}", error.into()))
        .context("ソースコードのコンパイルに失敗しました")
}

pub fn validation_err(error: impl Into<String>) -> Error {
    Error::msg(format!("検証エラー: {}", error.into()))
        .context("入力値や状態を確認してください")
} 