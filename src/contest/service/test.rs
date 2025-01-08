use std::path::{Path, PathBuf};
use anyhow::{Result as AnyhowResult, anyhow};
use crate::config::Config;
use crate::contest::model::Contest;
use crate::message::contest;
use crate::docker::execution::Runtime;

/// テスト結果の状態を表す列挙型
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum Status {
    Success,
    Failure,
    Error,
}

/// テストケースの結果を表す構造体
#[derive(Debug)]
pub struct CaseResult {
    pub case_number: usize,
    pub status: Status,
    pub execution_time: std::time::Duration,
    pub stdout: String,
    pub stderr: String,
    pub expected: String,
    pub actual: String,
}

/// テスト実行の結果を表す構造体
#[derive(Debug)]
#[allow(clippy::module_name_repetitions)]
pub struct TestResults {
    pub total_cases: usize,
    pub successful_cases: usize,
    pub failed_cases: usize,
    pub error_cases: usize,
    pub total_time: std::time::Duration,
    pub case_results: Vec<CaseResult>,
}

impl TestResults {
    /// テスト結果の概要を文字列として取得します
    #[must_use]
    pub fn summary(&self) -> String {
        format!(
            "テスト結果: {} テスト中 {} 成功, {} 失敗, {} エラー (合計時間: {:.2}秒)",
            self.total_cases,
            self.successful_cases,
            self.failed_cases,
            self.error_cases,
            self.total_time.as_secs_f64()
        )
    }
}

/// テスト実行サービスを提供する構造体
#[derive(Debug)]
pub struct Service {
    #[allow(dead_code)]
    config: Config,
    #[allow(dead_code)]
    runtime: Runtime,
}

impl Service {
    /// 新しいテストサービスを作成します
    /// 
    /// # Arguments
    /// * `config` - 設定情報
    /// 
    /// # Returns
    /// * `AnyhowResult<Self>` - 新しいテストサービスインスタンス
    /// 
    /// # Errors
    /// - 設定の読み込みに失敗した場合
    #[must_use = "この関数は新しいTestServiceインスタンスを返します"]
    pub fn new(config: &Config) -> AnyhowResult<Self> {
        Ok(Self {
            config: config.clone(),
            runtime: Runtime::new(),
        })
    }

    /// テストを実行します
    /// 
    /// # Arguments
    /// * `contest` - コンテスト情報
    /// * `test_number` - 実行するテストケース番号（Noneの場合は全テストを実行）
    /// 
    /// # Returns
    /// * `AnyhowResult<TestResults>` - テスト実行結果
    /// 
    /// # Errors
    /// - テストの実行に失敗した場合
    pub fn run_test(&self, contest: &Contest, test_number: Option<usize>) -> AnyhowResult<TestResults> {
        let test_dir = contest.get_test_dir()?;
        let source_file = contest.get_source_file()?;

        // テストケースの一覧を取得
        let test_cases = Self::get_test_cases(&test_dir, test_number)?;
        if test_cases.is_empty() {
            return Err(anyhow!(contest::error("test_failed", "テストケースが見つかりません")));
        }

        let start_time = std::time::Instant::now();
        let mut results = Vec::new();
        let mut successful_cases = 0;
        let mut failed_cases = 0;
        let mut error_cases = 0;
        let total_cases = test_cases.len();

        // 各テストケースを実行
        for (case_number, (input_file, expected_file)) in test_cases {
            match Self::run_test_case(case_number, &source_file, &input_file, &expected_file) {
                Ok(result) => {
                    match result.status {
                        Status::Success => successful_cases += 1,
                        Status::Failure => failed_cases += 1,
                        Status::Error => error_cases += 1,
                    }
                    results.push(result);
                }
                Err(e) => {
                    error_cases += 1;
                    results.push(CaseResult {
                        case_number,
                        status: Status::Error,
                        execution_time: std::time::Duration::from_secs(0),
                        stdout: String::new(),
                        stderr: e.to_string(),
                        expected: String::new(),
                        actual: String::new(),
                    });
                }
            }
        }

        Ok(TestResults {
            total_cases,
            successful_cases,
            failed_cases,
            error_cases,
            total_time: start_time.elapsed(),
            case_results: results,
        })
    }

    /// テストケースの一覧を取得します
    /// 
    /// # Arguments
    /// * `test_dir` - テストディレクトリ
    /// * `test_number` - 取得するテストケース番号（Noneの場合は全テスト）
    /// 
    /// # Returns
    /// * `AnyhowResult<Vec<(usize, (PathBuf, PathBuf))>>` - テストケース番号とテストファイルのペアのリスト
    /// 
    /// # Errors
    /// - テストケースの読み取りに失敗した場合
    fn get_test_cases(
        test_dir: &Path,
        test_number: Option<usize>,
    ) -> AnyhowResult<Vec<(usize, (PathBuf, PathBuf))>> {
        let mut cases = Vec::new();
        
        if let Some(n) = test_number {
            let input = test_dir.join(format!("{n}.in"));
            let expected = test_dir.join(format!("{n}.out"));
            if input.exists() && expected.exists() {
                cases.push((n, (input, expected)));
            }
        } else {
            for entry in std::fs::read_dir(test_dir)? {
                let entry = entry?;
                let path = entry.path();
                if let Some(ext) = path.extension() {
                    if ext == "in" {
                        if let Some(stem) = path.file_stem() {
                            if let Ok(n) = stem.to_string_lossy().parse::<usize>() {
                                let expected = test_dir.join(format!("{n}.out"));
                                if expected.exists() {
                                    cases.push((n, (path, expected)));
                                }
                            }
                        }
                    }
                }
            }
            cases.sort_by_key(|(n, _)| *n);
        }

        Ok(cases)
    }

    /// 単一のテストケースを実行します
    /// 
    /// # Arguments
    /// * `case_number` - テストケース番号
    /// * `source_file` - ソースファイル
    /// * `input_file` - 入力ファイル
    /// * `expected_file` - 期待される出力ファイル
    /// 
    /// # Returns
    /// * `AnyhowResult<CaseResult>` - テストケースの実実行結果
    /// 
    /// # Errors
    /// - テストケースの実行に失敗した場合
    fn run_test_case(
        case_number: usize,
        source_file: &Path,
        input_file: &Path,
        expected_file: &Path,
    ) -> AnyhowResult<CaseResult> {
        let start_time = std::time::Instant::now();

        // コンテナを作成して実行
        let mut runtime = Runtime::new().with_auto_remove(true);
        runtime.create("rust:latest", &[])?;
        let (stdout, stderr) = runtime.execute_command(&[
            "exec",
            source_file.to_string_lossy().as_ref(),
            "<",
            input_file.to_string_lossy().as_ref(),
        ])?;

        // 期待される出力を読み込み
        let expected = std::fs::read_to_string(expected_file)?;
        let actual = stdout.trim().to_string();

        // 結果を比較
        let status = if stderr.is_empty() && actual == expected.trim() {
            Status::Success
        } else if !stderr.is_empty() {
            Status::Error
        } else {
            Status::Failure
        };

        Ok(CaseResult {
            case_number,
            status,
            execution_time: start_time.elapsed(),
            stdout,
            stderr,
            expected,
            actual,
        })
    }
} 