use std::path::PathBuf;
use anyhow::Result;
use config::Config;

use super::command::run;

/// コンテナイメージのビルダー
#[derive(Debug)]
pub struct Builder {
    config: Config,
}

impl Builder {
    /// 新しいビルダーを作成する
    /// 
    /// # Arguments
    /// 
    /// * `config` - 設定
    /// 
    /// # Errors
    /// 
    /// * 設定の読み込みに失敗した場合
    pub const fn new(config: Config) -> Result<Self> {
        Ok(Self { config })
    }

    /// イメージをビルドする
    /// 
    /// # Arguments
    /// 
    /// * `tag` - イメージのタグ
    /// 
    /// # Errors
    /// 
    /// * イメージのビルドに失敗した場合
    pub async fn build_image(&self, tag: &str) -> Result<()> {
        let dockerfile = self.config.get::<PathBuf>("dockerfile")?;
        let context = self.config.get::<PathBuf>("context")?;

        run(
            "docker",
            &[
                "build",
                "-t",
                tag,
                "-f",
                &dockerfile.to_string_lossy(),
                &context.to_string_lossy(),
            ],
        )
        .await?;

        Ok(())
    }
} 