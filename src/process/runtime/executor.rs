use std::path::Path;
use anyhow::{Result, Context};
use crate::config::Config;
use crate::process::{ProcessExecutor, ProcessConfig};
use std::collections::HashMap;
use bytes::Bytes;

pub struct RuntimeExecutor {
    executor: ProcessExecutor,
    config: Config,
}

#[derive(Debug)]
pub struct ExecutionResult {
    pub exit_status: Option<std::process::ExitStatus>,
    pub output: Vec<Bytes>,
    pub timed_out: bool,
    pub memory_exceeded: bool,
}

impl RuntimeExecutor {
    pub fn new(config: Config) -> Self {
        Self {
            executor: ProcessExecutor::new(config.clone()),
            config,
        }
    }

    /// コンパイル済みのプログラムを実行し、結果を待ちます
    ///
    /// # Arguments
    ///
    /// * `language` - プログラミング言語
    /// * `executable_path` - 実行ファイルのパス
    /// * `args` - コマンドライン引数
    ///
    /// # Returns
    ///
    /// 実行結果
    pub async fn run_and_wait(&self, language: &str, executable_path: &Path, args: Vec<String>) -> Result<ExecutionResult> {
        let language_config = self.config.get_section(&format!("languages.{}", language))
            .context("言語設定の取得に失敗しました")?;

        let timeout_seconds: u64 = language_config.get("timeout_seconds")
            .unwrap_or(10);

        let mut run_command: Vec<String> = language_config.get("run")
            .context("実行コマンドの取得に失敗しました")?;

        // 実行コマンドを構築
        if run_command.len() == 1 {
            run_command.push(executable_path.to_string_lossy().to_string());
        }
        run_command.extend(args);

        let config = ProcessConfig {
            language: language.to_string(),
            command: run_command[0].clone(),
            args: run_command[1..].to_vec(),
            env_vars: HashMap::new(),
            working_dir: Some(executable_path.parent()
                .unwrap_or_else(|| Path::new("."))
                .to_string_lossy()
                .to_string()),
        };

        let process_id = self.executor.spawn(config).await?;

        // タイムアウト付きで実行結果を待つ
        let wait_result = self.executor.wait_with_timeout(&process_id, timeout_seconds).await;
        let output = self.executor.read_output(&process_id).await.unwrap_or_default();

        match wait_result {
            Ok(status) => Ok(ExecutionResult {
                exit_status: status.exit_status,
                output,
                timed_out: false,
                memory_exceeded: status.memory_exceeded,
            }),
            Err(e) if e.to_string().contains("タイムアウト") => Ok(ExecutionResult {
                exit_status: None,
                output,
                timed_out: true,
                memory_exceeded: false,
            }),
            Err(e) => Err(e),
        }
    }

    /// プロセスに入力を送信します
    pub async fn send_input(&self, process_id: &str, input: &str) -> Result<()> {
        self.executor.write_stdin(process_id, input).await
    }

    /// プロセスの出力を取得します
    pub async fn get_output(&self, process_id: &str) -> Option<Vec<Bytes>> {
        self.executor.read_output(process_id).await
    }

    /// プロセスを強制終了します
    pub async fn kill(&self, process_id: &str) -> Result<()> {
        self.executor.kill(process_id).await
    }
} 