use std::path::Path;
use anyhow::{Result, anyhow};
use async_trait::async_trait;
use cph::container::runtime::Runtime;

#[derive(Clone)]
pub struct MockRuntime {
    container_id: String,
    should_fail: bool,
}

impl MockRuntime {
    pub fn new(container_id: String) -> Self {
        Self { 
            container_id,
            should_fail: false,
        }
    }

    #[allow(dead_code)]
    pub fn with_failure(container_id: String) -> Self {
        Self {
            container_id,
            should_fail: true,
        }
    }
}

#[async_trait]
impl Runtime for MockRuntime {
    async fn create(
        &self,
        _image: &str,
        command: &[String],
        _working_dir: &Path,
        _env_vars: &[String],
    ) -> Result<String> {
        if self.should_fail {
            return Err(anyhow!("モックエラー: コンテナの作成に失敗しました"));
        }

        // rustcコマンドの場合はコンパイルエラーを返す
        if command.get(0).map_or(false, |cmd| cmd == "rustc") {
            return Err(anyhow!("コンパイルエラー: 無効なソースコード"));
        }

        // python -c で実行時エラーを含むコマンドの場合
        if command.get(0).map_or(false, |cmd| cmd == "python") 
            && command.get(1).map_or(false, |arg| arg == "-c")
            && command.get(2).map_or(false, |code| code.contains("raise Exception")) {
            return Err(anyhow!("実行時エラー: Python例外が発生しました"));
        }

        Ok(self.container_id.clone())
    }

    async fn start(&self, _container_id: &str) -> Result<()> {
        if self.should_fail {
            return Err(anyhow!("モックエラー: コンテナの起動に失敗しました"));
        }
        Ok(())
    }

    async fn stop(&self, _container_id: &str) -> Result<()> {
        Ok(())
    }

    async fn remove(&self, _container_id: &str) -> Result<()> {
        Ok(())
    }

    fn box_clone(&self) -> Box<dyn Runtime> {
        Box::new(self.clone())
    }
} 