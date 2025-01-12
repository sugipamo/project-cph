use std::time::Instant;
use anyhow::{Result, Context};
use crate::process::{ProcessExecutor, ProcessConfig};
use crate::process::test::{TestCase, TestResult, TestSuite};
use std::collections::HashMap;

pub struct TestRunner {
    executor: ProcessExecutor,
}

impl TestRunner {
    pub fn new(executor: ProcessExecutor) -> Self {
        Self { executor }
    }

    pub async fn run_test(&self, language: &str, test_case: &TestCase, executable: &str) -> Result<TestResult> {
        let start_time = Instant::now();

        // プロセス設定
        let config = ProcessConfig {
            language: language.to_string(),
            command: executable.to_string(),
            args: vec![],
            env_vars: HashMap::new(),
            working_dir: None,
        };

        // プロセス実行
        let process_id = self.executor.spawn(config).await?;

        // 入力を送信
        self.executor.write_stdin(&process_id, &test_case.input).await?;

        // 実行結果を待機
        let timeout = test_case.time_limit.unwrap_or(10);
        let status = self.executor.wait_with_timeout(&process_id, timeout).await?;

        // 出力を取得
        let output = self.executor.read_output(&process_id)
            .await
            .unwrap_or_default()
            .into_iter()
            .flat_map(|b| b.to_vec())
            .collect::<Vec<_>>();

        // 実行時間を計算
        let execution_time = start_time.elapsed().as_millis() as u64;

        // クリーンアップ
        self.executor.cleanup(&process_id).await?;

        // 結果を検証
        if let Some(exit_status) = status.exit_status {
            if !exit_status.success() {
                return Ok(TestResult::failure(
                    output,
                    execution_time,
                    None,
                    format!("プロセスが異常終了しました（終了コード: {}）", exit_status.code().unwrap_or(-1))
                ));
            }
        }

        if status.memory_exceeded {
            return Ok(TestResult::failure(
                output,
                execution_time,
                None,
                "メモリ制限を超過しました".to_string()
            ));
        }

        // 出力を比較
        let actual_output = String::from_utf8_lossy(&output);
        if self.normalize_output(&actual_output) != self.normalize_output(&test_case.expected_output) {
            return Ok(TestResult::failure(
                output,
                execution_time,
                None,
                "出力が一致しません".to_string()
            ));
        }

        Ok(TestResult::success(output, execution_time, None))
    }

    pub async fn run_suite(&self, language: &str, suite: &TestSuite) -> Result<Vec<TestResult>> {
        let mut results = Vec::new();

        for test_case in &suite.test_cases {
            let result = self.run_test(language, test_case, &suite.source_file.to_string_lossy())
                .await
                .context("テストケースの実行に失敗しました")?;
            results.push(result);
        }

        Ok(results)
    }

    fn normalize_output(&self, output: &str) -> String {
        output
            .trim()
            .lines()
            .map(str::trim)
            .collect::<Vec<_>>()
            .join("\n")
    }
} 