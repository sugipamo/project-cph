use std::path::{Path, PathBuf};
use anyhow::{Result, Context};
use crate::config::Config;
use crate::process::ProcessExecutor;
use crate::process::ProcessConfig;
use std::collections::HashMap;

pub struct Compiler {
    executor: ProcessExecutor,
    config: Config,
}

impl Compiler {
    pub fn new(config: Config) -> Self {
        Self {
            executor: ProcessExecutor::new(config.clone()),
            config,
        }
    }

    /// ソースコードをコンパイルします
    ///
    /// # Arguments
    ///
    /// * `language` - プログラミング言語
    /// * `source_path` - ソースファイルのパス
    /// * `output_dir` - 出力ディレクトリ
    ///
    /// # Returns
    ///
    /// コンパイル結果のパス
    pub async fn compile(&self, language: &str, source_path: &Path, output_dir: &Path) -> Result<PathBuf> {
        let language_config = self.config.get_section(&format!("languages.{}", language))
            .context("言語設定の取得に失敗しました")?;

        // コンパイルが必要ない言語の場合はソースをそのまま返す
        let compile_command: Vec<String> = language_config.get("compile")
            .unwrap_or_default();
        if compile_command.is_empty() {
            return Ok(source_path.to_path_buf());
        }

        // 出力ファイル名を生成
        let output_file = output_dir.join(
            source_path.file_stem()
                .ok_or_else(|| anyhow::anyhow!("ソースファイル名が不正です"))?
        );

        // コンパイルコマンドを構築
        let mut args = compile_command[1..].to_vec();
        args.push(source_path.to_string_lossy().to_string());
        args.push("-o".to_string());
        args.push(output_file.to_string_lossy().to_string());

        let config = ProcessConfig {
            language: language.to_string(),
            command: compile_command[0].clone(),
            args,
            env_vars: HashMap::new(),
            working_dir: Some(output_dir.to_string_lossy().to_string()),
        };

        // コンパイル実行
        let process_id = self.executor.spawn(config).await?;
        let status = self.executor.wait(&process_id).await?;

        if !status.success() {
            let error_output = self.executor.read_output(&process_id).await
                .unwrap_or_default();
            let error_message = String::from_utf8_lossy(&error_output.concat());
            anyhow::bail!("コンパイルに失敗しました: {}", error_message);
        }

        Ok(output_file)
    }
} 