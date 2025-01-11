use std::path::{Path, PathBuf};
use anyhow::{Result as AnyhowResult, anyhow};
use crate::contest::model::Contest;
use crate::message::contest;

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
#[derive(Debug, Default)]
pub struct Service {}

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
    pub const fn new(_config: &crate::config::Config) -> AnyhowResult<Self> {
        Ok(Self {})
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

        for (case_number, (input_file, expected_file)) in test_cases {
            let result = Self::run_test_case(case_number, &source_file, &input_file, &expected_file)?;
            
            match result.status {
                Status::Success => successful_cases += 1,
                Status::Failure => failed_cases += 1,
                Status::Error => error_cases += 1,
            }
            
            results.push(result);
        }

        let total_time = start_time.elapsed();

        Ok(TestResults {
            total_cases: results.len(),
            successful_cases,
            failed_cases,
            error_cases,
            total_time,
            case_results: results,
        })
    }

    /// テストケースの一覧を取得します
    fn get_test_cases(
        test_dir: &Path,
        test_number: Option<usize>,
    ) -> AnyhowResult<Vec<(usize, (PathBuf, PathBuf))>> {
        let mut test_cases = Vec::new();
        
        if !test_dir.exists() {
            return Ok(test_cases);
        }

        let entries = std::fs::read_dir(test_dir)?;
        
        for entry in entries {
            let entry = entry?;
            let path = entry.path();
            
            if path.is_file() {
                if let Some(file_name) = path.file_name().and_then(|n| n.to_str()) {
                    if let Some(case_number) = Self::parse_test_case_number(file_name) {
                        if let Some(test_num) = test_number {
                            if case_number != test_num {
                                continue;
                            }
                        }
                        
                        let input_file = test_dir.join(format!("{case_number}.in"));
                        let expected_file = test_dir.join(format!("{case_number}.out"));
                        
                        if input_file.exists() && expected_file.exists() {
                            test_cases.push((case_number, (input_file, expected_file)));
                        }
                    }
                }
            }
        }

        test_cases.sort_by_key(|(num, _)| *num);
        Ok(test_cases)
    }

    /// テストケース番号をパースします
    fn parse_test_case_number(file_name: &str) -> Option<usize> {
        file_name.split('.').next().and_then(|base_name| base_name.parse().ok())
    }

    /// テストケースを実行します
    fn run_test_case(
        case_number: usize,
        _source_file: &Path,
        _input_file: &Path,
        expected_file: &Path,
    ) -> AnyhowResult<CaseResult> {
        // TODO: 実際のテスト実行を実装
        let start_time = std::time::Instant::now();
        let execution_time = start_time.elapsed();

        // 期待される出力を読み込む
        let expected = std::fs::read_to_string(expected_file)?;

        Ok(CaseResult {
            case_number,
            status: Status::Success, // 仮の実装
            execution_time,
            stdout: String::new(),
            stderr: String::new(),
            expected,
            actual: String::new(),
        })
    }

    /// 設定を使用してテストを実行します
    /// 
    /// # Arguments
    /// 
    /// * `contest` - コンテスト情報
    /// * `test_number` - テスト番号（オプション）
    /// * `test_dir` - テストディレクトリ
    /// 
    /// # Returns
    /// 
    /// * `AnyhowResult<TestResults>` - テスト結果
    /// 
    /// # Errors
    /// 
    /// - テストの実行に失敗した場合
    pub fn run_test_with_config(
        &self,
        contest: &Contest,
        test_number: Option<usize>,
        _test_dir: &str,
    ) -> AnyhowResult<TestResults> {
        self.run_test(contest, test_number)
    }
} 