use std::path::PathBuf;
use anyhow::Result;
use config::Config;

use crate::container::registry::Builder;

/// コンテナランタイムの設定を管理する構造体
#[derive(Debug)]
pub struct Settings {
    config: Config,
}

impl Settings {
    /// 新しいランタイム設定を作成する
    /// 
    /// # Arguments
    /// 
    /// * `config_path` - 設定ファイルのパス
    /// 
    /// # Errors
    /// 
    /// * 設定ファイルの読み込みに失敗した場合
    pub fn new(config_path: PathBuf) -> Result<Self> {
        let config = Config::builder()
            .add_source(config::File::from(config_path))
            .build()?;

        Ok(Self { config })
    }

    /// コンテナビルダーを作成する
    /// 
    /// # Errors
    /// 
    /// * コンテナビルダーの作成に失敗した場合
    pub fn create_builder(&self) -> Result<Builder> {
        Builder::new(self.config.clone())
    }
} 