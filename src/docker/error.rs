use anyhow::{Error, Context as _};

pub type DockerResult<T> = Result<T, Error>;

pub fn docker_err(error: impl Into<String>, message: impl Into<String>) -> Error {
    Error::msg(format!("{}: {}", message.into(), error.into()))
        .context("Dockerの操作に失敗しました")
}

pub fn execution_err(_: impl Into<String>, message: impl Into<String>) -> Error {
    Error::msg(format!("実行エラー: {}", message.into()))
        .context("Dockerコンテナの実行に失敗しました")
}

pub fn compilation_err(_: impl Into<String>, message: impl Into<String>) -> Error {
    Error::msg(format!("コンパイルエラー: {}", message.into()))
        .context("ソースコードのコンパイルに失敗しました")
}

pub fn container_err(_: impl Into<String>, message: impl Into<String>) -> Error {
    Error::msg(format!("コンテナエラー: {}", message.into()))
        .context("Dockerコンテナが見つかりません")
}

pub fn state_err(_: impl Into<String>, message: impl Into<String>) -> Error {
    Error::msg(format!("状態エラー: {}", message.into()))
        .context("コンテナの状態が不正です")
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_docker_err() {
        let error = docker_err("テストエラー", "テスト操作");
        assert!(error.to_string().contains("テストエラー"));
        assert!(error.to_string().contains("テスト操作"));
        assert!(error.to_string().contains("Dockerの操作に失敗しました"));
    }

    #[test]
    fn test_execution_err() {
        let error = execution_err("", "テスト実行エラー");
        assert!(error.to_string().contains("テスト実行エラー"));
        assert!(error.to_string().contains("Dockerコンテナの実行に失敗しました"));
    }

    #[test]
    fn test_compilation_err() {
        let error = compilation_err("", "テストコンパイルエラー");
        assert!(error.to_string().contains("テストコンパイルエラー"));
        assert!(error.to_string().contains("ソースコードのコンパイルに失敗しました"));
    }

    #[test]
    fn test_container_err() {
        let error = container_err("", "テストコンテナエラー");
        assert!(error.to_string().contains("テストコンテナエラー"));
        assert!(error.to_string().contains("Dockerコンテナが見つかりません"));
    }

    #[test]
    fn test_state_err() {
        let error = state_err("", "テスト状態エラー");
        assert!(error.to_string().contains("テスト状態エラー"));
        assert!(error.to_string().contains("コンテナの状態が不正です"));
    }
} 