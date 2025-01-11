use std::path::PathBuf;
use serde::{Deserialize, Serialize};
use anyhow::{Result, Context};
use crate::config::Config;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ContainerConfig {
    pub image: String,
    pub command: Vec<String>,
    pub working_dir: PathBuf,
    pub env_vars: Vec<String>,
    pub timeout_sec: Option<u64>,
    pub memory_limit_mb: Option<u64>,
    pub mount_point: Option<String>,
}

impl ContainerConfig {
    pub fn new(
        image: String,
        command: Vec<String>,
        working_dir: PathBuf,
        env_vars: Vec<String>,
        timeout_sec: Option<u64>,
        memory_limit_mb: Option<u64>,
        mount_point: Option<String>,
    ) -> Self {
        Self {
            image,
            command,
            working_dir,
            env_vars,
            timeout_sec,
            memory_limit_mb,
            mount_point,
        }
    }

    /// 設定ファイルから言語固有の設定を読み込んでContainerConfigを作成します
    pub fn from_language(
        language: &str,
        source_file: &str,
        working_dir: PathBuf,
    ) -> Result<Self> {
        let config = Config::load()?;
        
        // 言語固有の設定を取得
        let image = config.get_language_image(language)?;
        let env_vars = config.get_language_env_vars(language)?;
        let docker_config = config.get_language_docker_config(language)?;

        // コマンドを構築
        let mut command = Vec::new();
        if let Ok(compile_cmd) = config.get_language_compile_command(language) {
            command.extend(compile_cmd);
        }
        command.extend(config.get_language_run_command(language)?);
        command.push(source_file.to_string());

        Ok(Self::new(
            image,
            command,
            working_dir,
            env_vars,
            Some(u64::from(docker_config.timeout_seconds)),
            Some(u64::from(docker_config.memory_limit_mb)),
            Some(docker_config.mount_point.clone()),
        ))
    }
} 