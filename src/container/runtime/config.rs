use std::path::PathBuf;
use serde::{Deserialize, Serialize};
use anyhow::Result;
use crate::config::Config as GlobalConfig;
use crate::container::image_builder::BuilderConfig;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ImageSpec {
    pub image_type: String,
    pub source: String,
}

impl ImageSpec {
    pub fn new(image_type: impl Into<String>, source: impl Into<String>) -> Self {
        Self {
            image_type: image_type.into(),
            source: source.into(),
        }
    }

    /// コンテナビルダーの設定に変換します。
    ///
    /// # Returns
    /// `BuilderConfig` - ビルダーの設定
    #[must_use]
    pub fn to_builder_config(&self) -> BuilderConfig {
        BuilderConfig::new(self.image_type.clone(), self.source.clone())
    }

    /// イメージを準備します。
    ///
    /// # Arguments
    /// * `tag` - イメージのタグ
    ///
    /// # Returns
    /// * `Ok(String)` - 準備されたイメージのID
    /// * `Err(_)` - イメージの準備に失敗した場合
    ///
    /// # Errors
    /// * イメージのビルドに失敗した場合
    /// * イメージのプルに失敗した場合
    pub async fn prepare_image(&self, tag: &str) -> Result<String> {
        let builder_config = self.to_builder_config();
        if let Some(builder) = builder_config.create_builder() {
            builder.build_image(tag).await?;
            Ok(tag.to_string())
        } else {
            Ok(self.source.clone())
        }
    }
}

#[derive(Debug, Clone)]
pub struct Config {
    pub id: String,
    pub image: String,
    pub working_dir: PathBuf,
    pub args: Vec<String>,
    pub image_config: Option<ImageSpec>,
}

impl Default for Config {
    fn default() -> Self {
        Self {
            id: String::new(),
            image: String::new(),
            working_dir: PathBuf::from("/compile"),
            args: Vec::new(),
            image_config: None,
        }
    }
}

impl Config {
    pub fn new(
        id: impl Into<String>,
        image: impl Into<String>,
        working_dir: impl Into<PathBuf>,
        args: Vec<String>,
        image_config: Option<ImageSpec>,
    ) -> Self {
        Self {
            id: id.into(),
            image: image.into(),
            working_dir: working_dir.into(),
            args,
            image_config,
        }
    }

    /// イメージを準備し、準備されたイメージ名を含む新しい設定を返します。
    ///
    /// # Returns
    /// * `Ok(Self)` - 準備されたイメージを含む新しい設定
    /// * `Err(_)` - イメージの準備に失敗した場合
    ///
    /// # Errors
    /// * イメージのビルドに失敗した場合
    /// * イメージのプルに失敗した場合
    pub async fn prepare_image(&self) -> Result<Self> {
        let image = if let Some(image_config) = &self.image_config {
            let tag = format!("cph-{}", self.id);
            image_config.prepare_image(&tag).await?
        } else {
            self.image.clone()
        };

        Ok(Self {
            id: self.id.clone(),
            image,
            working_dir: self.working_dir.clone(),
            args: self.args.clone(),
            image_config: self.image_config.clone(),
        })
    }
}

#[derive(Clone, Debug)]
pub struct ResourceLimits {
    pub memory_mb: u64,
    pub cpu_count: u32,
    pub timeout_sec: u32,
}

impl Default for ResourceLimits {
    fn default() -> Self {
        // グローバル設定から値を取得
        if let Ok(config) = GlobalConfig::get_default_config() {
            if let Ok(memory) = config.get::<u64>("system.container.memory_limit_mb") {
                if let Ok(timeout) = config.get::<u32>("system.container.timeout_seconds") {
                    return Self {
                        memory_mb: memory,
                        cpu_count: 1,
                        timeout_sec: timeout,
                    };
                }
            }
        }

        // フォールバック値
        Self {
            memory_mb: 512,
            cpu_count: 1,
            timeout_sec: 30,
        }
    }
}

/// containerdの設定を取得します
/// 
/// # Returns
/// 
/// * `Result<(String, String)>` - (ソケットパス, ネームスペース)のタプル
/// 
/// # Errors
/// 
/// 以下の場合にエラーを返します：
/// - 設定ファイルの読み込みに失敗した場合
/// - 必要な設定値が見つからない場合
/// - 設定値の型変換に失敗した場合
#[allow(clippy::module_name_repetitions)]
pub fn get_runtime_config() -> Result<(String, String)> {
    let config = GlobalConfig::get_default_config()?;
    let socket = config.get::<String>("system.container.runtime.containerd.socket")?;
    let namespace = config.get::<String>("system.container.runtime.containerd.namespace")?;
    Ok((socket, namespace))
} 