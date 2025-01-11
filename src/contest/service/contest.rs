use anyhow::{Result as AnyhowResult};

/// コンテストサービスを提供する構造体
#[derive(Clone, Default)]
pub struct Service {}

impl Service {
    /// 新しいコンテストサービスを作成します
    /// 
    /// # Arguments
    /// * `config` - 設定情報
    /// 
    /// # Returns
    /// * `AnyhowResult<Self>` - 新しいコンテストサービスインスタンス
    /// 
    /// # Errors
    /// - 設定の読み込みに失敗した場合
    #[must_use = "この関数は新しいContestServiceインスタンスを返します"]
    pub const fn new(_config: &crate::config::Config) -> AnyhowResult<Self> {
        Ok(Self {})
    }
} 