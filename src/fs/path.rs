use std::path::{Path, PathBuf};
use anyhow::{Result, anyhow};
use crate::message::fs as fs_message;

/// パスの検証レベルを定義する列挙型
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum ValidationLevel {
    /// 基本的な検証のみ（絶対パスとパストラバーサルのチェック）
    Basic,
    /// 厳格な検証（Basic + 特殊文字、非ASCII文字、長さ制限など）
    Strict,
}

/// パス操作に関する共通機能を提供する構造体
#[derive(Debug)]
#[allow(dead_code)]
pub struct Validator {
    /// パスの検証レベル
    validation_level: ValidationLevel,
    /// パス長の最大値（バイト単位）
    max_path_length: usize,
    /// ファイル名の最大長（バイト単位）
    max_filename_length: usize,
}

impl Default for Validator {
    #[must_use = "この関数は新しいValidatorインスタンスを返します"]
    fn default() -> Self {
        Self {
            validation_level: ValidationLevel::Basic,
            max_path_length: 4096,
            max_filename_length: 255,
        }
    }
}

impl Validator {
    /// 新しいValidatorインスタンスを作成します
    ///
    /// # Arguments
    /// * `validation_level` - パスの検証レベル
    /// * `max_path_length` - パス長の最大値（バイト単位）
    /// * `max_filename_length` - ファイル名の最大長（バイト単位）
    #[must_use = "この関数は新しいValidatorインスタンスを返します"]
    pub const fn new(
        validation_level: ValidationLevel,
        max_path_length: usize,
        max_filename_length: usize,
    ) -> Self {
        Self {
            validation_level,
            max_path_length,
            max_filename_length,
        }
    }

    /// パスを検証します
    ///
    /// # Errors
    ///
    /// 以下の場合にエラーを返します：
    /// - パストラバーサルが検出された場合
    /// - 絶対パスが使用された場合
    /// - ファイル名が長すぎる場合
    pub fn validate(&self, path: impl AsRef<Path>) -> Result<()> {
        let path = path.as_ref();

        // パストラバーサルのチェック
        if path.components().any(|c| c.as_os_str() == "..") {
            return Err(anyhow!(fs_message::error("path_traversal_error", "パストラバーサルは許可されていません")));
        }

        // 絶対パスのチェック
        if path.is_absolute() {
            return Err(anyhow!(fs_message::error("absolute_path_error", "絶対パスは許可されていません")));
        }

        // ファイル名の長さチェック
        if let Some(filename) = path.file_name() {
            if filename.len() > self.max_filename_length {
                return Err(anyhow!(fs_message::error("filename_too_long", format!("ファイル名が長すぎます（最大{}バイト）", self.max_filename_length))));
            }
        }

        Ok(())
    }

    /// パスを正規化します
    /// 
    /// # Arguments
    /// * `root` - ルートディレクトリのパス
    /// * `path` - 正規化するパス
    /// 
    /// # Returns
    /// * `Result<PathBuf>` - 正規化されたパス
    /// 
    /// # Errors
    /// * パスの検証に失敗した場合
    /// * パスの正規化に失敗した場合
    #[must_use = "この関数は正規化されたパスを返します"]
    pub fn normalize<P1: AsRef<Path>, P2: AsRef<Path>>(&self, root: P1, path: P2) -> Result<PathBuf> {
        // パスの検証
        self.validate(path.as_ref())?;

        // パスの正規化
        let normalized = path.as_ref().strip_prefix(".").unwrap_or_else(|_| path.as_ref());
        Ok(root.as_ref().join(normalized))
    }
}

/// パスを正規化します
/// 
/// # Arguments
/// * `root` - ルートディレクトリのパス
/// * `path` - 正規化するパス
/// 
/// # Returns
/// * `Result<PathBuf>` - 正規化されたパス
/// 
/// # Errors
/// * パスの検証に失敗した場合
/// * パスの正規化に失敗した場合
pub fn normalize<P1: AsRef<Path>, P2: AsRef<Path>>(root: P1, path: P2) -> Result<PathBuf> {
    Validator::default().normalize(root, path)
}

/// パスを検証します
/// 
/// # Arguments
/// * `path` - 検証するパス
/// 
/// # Returns
/// * `Result<()>` - 検証結果
/// 
/// # Errors
/// * パスが無効な場合
pub fn validate<P: AsRef<Path>>(path: P) -> Result<()> {
    Validator::default().validate(path)
}

/// パスが存在することを確認し、存在しない場合はディレクトリを作成します。
/// 
/// # Arguments
/// * `path` - 確認または作成するパス
/// 
/// # Errors
/// - ディレクトリの作成に失敗した場合
pub fn ensure_path_exists(path: impl AsRef<Path>) -> Result<()> {
    let path = path.as_ref();
    if !path.exists() {
        std::fs::create_dir_all(path)
            .map_err(|e| anyhow!("ディレクトリの作成に失敗しました: {e}"))?;
    }
    Ok(())
} 