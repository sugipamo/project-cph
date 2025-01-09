use async_trait::async_trait;
use anyhow::{Result, anyhow};
use std::process::Command;
use crate::container::runtime::interface::image::{ImageManager, ImageInfo, ImageDetails};

pub struct BaseImageManager {
    command_name: String,
}

impl BaseImageManager {
    pub fn new(command_name: impl Into<String>) -> Self {
        Self {
            command_name: command_name.into(),
        }
    }

    /// 基本的なコマンド実行機能
    pub async fn execute_command(&self, args: &[&str]) -> Result<(String, String)> {
        let output = Command::new(&self.command_name)
            .args(args)
            .output()
            .map_err(|e| anyhow!("コマンドの実行に失敗: {}", e))?;

        let stdout = String::from_utf8_lossy(&output.stdout).to_string();
        let stderr = String::from_utf8_lossy(&output.stderr).to_string();

        if !output.status.success() {
            return Err(anyhow!("コマンドがエラーを返しました: {}", stderr));
        }

        Ok((stdout, stderr))
    }

    /// イメージ名の変換（オーバーライド可能）
    pub fn convert_image_name(&self, image_name: &str) -> Result<String> {
        Ok(image_name.to_string())
    }

    /// イメージ情報のパース（オーバーライド必須）
    pub fn parse_image_info(&self, _line: &str) -> Option<ImageInfo> {
        None
    }
} 