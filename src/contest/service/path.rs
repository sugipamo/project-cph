use std::path::{Path, PathBuf};
use anyhow::{Result, anyhow};
use crate::message::contest;

/// パスの種類を表す列挙型
#[derive(Debug, Clone, Copy)]
pub enum Type {
    Contest,
    Problem,
    Source,
    Test,
}

impl Type {
    /// パスの種類を文字列として取得します
    const fn as_str(self) -> &'static str {
        match self {
            Self::Contest => "コンテスト",
            Self::Problem => "問題",
            Self::Source => "ソース",
            Self::Test => "テスト",
        }
    }
}

/// パス管理サービスを提供する構造体
#[derive(Debug)]
pub struct Service {
    #[allow(dead_code)]
    base_dir: PathBuf,
}

impl Service {
    /// 新しいパス管理サービスを作成します
    ///
    /// # Arguments
    /// * `base_dir` - ベースディレクトリ
    ///
    /// # Returns
    /// * `Self` - 新しいパス管理サービスインスタンス
    #[must_use = "この関数は新しいPathServiceインスタンスを返します"]
    pub fn new(base_dir: impl AsRef<Path>) -> Self {
        Self {
            base_dir: base_dir.as_ref().to_path_buf(),
        }
    }

    /// パスの存在を検証します
    ///
    /// # Arguments
    /// * `path` - 検証するパス
    /// * `path_type` - パスの種類
    ///
    /// # Returns
    /// * `Result<()>` - 検証結果
    ///
    /// # Errors
    /// * パスが存在しない場合
    pub fn validate_path_exists(path: impl AsRef<Path>, path_type: Type) -> Result<()> {
        let path = path.as_ref();
        if !path.exists() {
            return Err(anyhow!(contest::error(
                "path_error",
                format!("{}ディレクトリが存在しません: {}", path_type.as_str(), path.display())
            )));
        }
        Ok(())
    }

    /// ディレクトリを作成します
    ///
    /// # Arguments
    /// * `path` - 作成するディレクトリのパス
    /// * `path_type` - パスの種類
    ///
    /// # Returns
    /// * `Result<()>` - 作成結果
    ///
    /// # Errors
    /// * ディレクトリの作成に失敗した場合
    pub fn create_directory(path: impl AsRef<Path>, path_type: Type) -> Result<()> {
        let path = path.as_ref();
        if !path.exists() {
            std::fs::create_dir_all(path)
                .map_err(|e| anyhow!(contest::error(
                    "path_error",
                    format!("{}ディレクトリの作成に失敗: {}: {}", path_type.as_str(), path.display(), e)
                )))?;
        }
        Ok(())
    }
}