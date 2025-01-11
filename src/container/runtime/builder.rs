use super::{Container, Runtime};
use super::config::Config;
use std::sync::Arc;
use std::path::PathBuf;
use anyhow::Result;

pub struct ContainerBuilder {
    config: Config,
    runtime: Option<Arc<dyn Runtime>>,
}

impl ContainerBuilder {
    pub fn new() -> Self {
        Self {
            config: Config::default(),
            runtime: None,
        }
    }

    pub fn with_id(mut self, id: impl Into<String>) -> Self {
        self.config.id = id.into();
        self
    }

    pub fn with_image(mut self, image: impl Into<String>) -> Self {
        self.config.image = image.into();
        self
    }

    pub fn with_runtime(mut self, runtime: Arc<dyn Runtime>) -> Self {
        self.runtime = Some(runtime);
        self
    }

    pub fn with_args(mut self, args: Vec<String>) -> Self {
        self.config.args = args;
        self
    }

    pub fn with_working_dir(mut self, working_dir: impl Into<PathBuf>) -> Self {
        self.config.working_dir = working_dir.into();
        self
    }

    /// 指定された言語用のコンテナをビルドします
    pub fn build_for_language(
        mut self,
        language: &str,
        source_file: &str,
        args: Vec<String>
    ) -> Result<Container> {
        println!("ContainerBuilder: build_for_language開始 (language={}, source={})", language, source_file);
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

    pub fn build(self) -> Container {
        println!("ContainerBuilder: ランタイムでコンテナを構築");
        let runtime = self.runtime.expect("ランタイムが設定されていません");
        let container = Container::new(runtime, self.config);
        println!("ContainerBuilder: コンテナ構築完了 (id={})", container.id());
        container
    }
}

impl Default for ContainerBuilder {
    fn default() -> Self {
        Self::new()
    }
} 