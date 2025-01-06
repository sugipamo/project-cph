use crate::config::Config;
use crate::docker::error::{DockerError, DockerResult};

#[derive(Debug, Clone)]
pub struct DockerConfig {
    timeout_seconds: u32,
    memory_limit: u32,
    mount_point: String,
    image: String,
    extension: String,
    compile_cmd: Option<Vec<String>>,
    run_cmd: Vec<String>,
}

impl DockerConfig {
    pub fn new(config: &Config, language: &str) -> DockerResult<Self> {
        let base_path = format!("languages.{}.runner", language);
        
        // 言語の存在確認
        let extension = config
            .get::<String>(&format!("languages.{}.extension", language))
            .map_err(|e| DockerError::Config(format!("言語名の解決に失敗しました: {}", e)))?;

        // Docker設定の取得
        let docker_path = format!("{}.docker", base_path);
        let timeout_seconds = config
            .get::<u64>(&format!("{}.timeout_seconds", docker_path))
            .unwrap_or(10) as u32;
        
        let memory_limit = config
            .get::<u64>(&format!("{}.memory_limit_mb", docker_path))
            .unwrap_or(256) as u32;
        
        let mount_point = config
            .get::<String>(&format!("{}.mount_point", docker_path))
            .unwrap_or_else(|_| "/compile".to_string());

        // イメージ名を取得
        let image = config
            .get::<String>(&format!("{}.image", base_path))
            .map_err(|e| DockerError::Config(format!("イメージ名の取得に失敗しました: {}", e)))?;

        // コマンドを取得
        let compile_cmd = config
            .get::<Vec<String>>(&format!("{}.compile", base_path))
            .ok();

        let run_cmd = config
            .get::<Vec<String>>(&format!("{}.run", base_path))
            .map_err(|e| DockerError::Config(format!("実行コマンドの取得に失敗しました: {}", e)))?;

        Ok(Self {
            timeout_seconds,
            memory_limit,
            mount_point,
            image,
            extension,
            compile_cmd,
            run_cmd,
        })
    }

    pub fn timeout_seconds(&self) -> u32 {
        self.timeout_seconds
    }

    pub fn memory_limit(&self) -> u32 {
        self.memory_limit
    }

    pub fn mount_point(&self) -> &str {
        &self.mount_point
    }

    pub fn image(&self) -> &str {
        &self.image
    }

    pub fn extension(&self) -> &str {
        &self.extension
    }

    pub fn compile_cmd(&self) -> Option<&[String]> {
        self.compile_cmd.as_deref()
    }

    pub fn run_cmd(&self) -> &[String] {
        &self.run_cmd
    }
} 