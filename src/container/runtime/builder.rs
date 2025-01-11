use super::{Container, Runtime};
use super::config::Config;
use std::sync::Arc;
use std::path::PathBuf;
use anyhow::Result;

pub struct Builder {
    config: Config,
    runtime: Option<Arc<dyn Runtime>>,
}

impl Builder {
    #[must_use]
    pub fn new() -> Self {
        Self {
            config: Config::default(),
            runtime: None,
        }
    }

    #[must_use]
    pub fn with_id(mut self, id: impl Into<String>) -> Self {
        self.config.id = id.into();
        self
    }

    #[must_use]
    pub fn with_image(mut self, image: impl Into<String>) -> Self {
        self.config.image = image.into();
        self
    }

    #[must_use]
    pub fn with_runtime(mut self, runtime: Arc<dyn Runtime>) -> Self {
        self.runtime = Some(runtime);
        self
    }

    #[must_use]
    pub fn with_args(mut self, args: Vec<String>) -> Self {
        self.config.args = args;
        self
    }

    #[must_use]
    pub fn with_working_dir(mut self, working_dir: impl Into<PathBuf>) -> Self {
        self.config.working_dir = working_dir.into();
        self
    }

    /// 指定された言語用のコンテナをビルドします
    /// 
    /// # Errors
    /// 
    /// 以下の場合にエラーを返します：
    /// - ランタイムの初期化に失敗した場合
    /// - コンテナの構築に失敗した場合
    /// - 言語がサポートされていない場合
    pub fn build_for_language(
        mut self,
        language: &str,
        source_file: &str,
        args: Vec<String>
    ) -> Result<Container> {
        println!("ContainerBuilder: build_for_language開始 (language={language}, source={source_file})");
        self.config.args = args;
        self.config.working_dir = PathBuf::from(source_file);

        match language {
            "python" => {
                self.config.image = "python:3.9".to_string();
                println!("ContainerBuilder: Pythonイメージを設定");
            }
            "rust" => {
                self.config.image = "rust:1.70".to_string();
                println!("ContainerBuilder: Rustイメージを設定");
            }
            _ => return Err(anyhow::anyhow!("サポートされていない言語です: {}", language)),
        }

        if self.config.id.is_empty() {
            self.config.id = uuid::Uuid::new_v4().to_string();
            println!("ContainerBuilder: 新しいID生成: {}", self.config.id);
        }

        println!("ContainerBuilder: コンテナをビルド");
        Ok(self.build())
    }

    /// コンテナをビルドします。
    /// 
    /// # Panics
    /// 
    /// - ランタイムが設定されていない場合にパニックします。
    pub fn build(self) -> Container {
        println!("ContainerBuilder: build開始");
        let runtime = self.runtime.expect("ランタイムが設定されていません");
        Container::new(runtime, self.config)
    }
}

impl Default for Builder {
    fn default() -> Self {
        Self::new()
    }
} 