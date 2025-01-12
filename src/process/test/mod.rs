mod runner;

pub use runner::Runner;

/// テストケースを表す構造体
#[derive(Debug, Clone)]
pub struct Case {
    pub input: String,
    pub expected_output: String,
    pub timeout_secs: Option<u64>,
    pub memory_limit_mb: Option<u64>,
}

impl Case {
    /// 新しいテストケースを作成する
    /// 
    /// # Arguments
    /// 
    /// * `input` - テストの入力データ
    /// * `expected_output` - 期待される出力
    #[must_use]
    pub const fn new(input: String, expected_output: String) -> Self {
        Self {
            input,
            expected_output,
            timeout_secs: None,
            memory_limit_mb: None,
        }
    }

    /// 制限付きのテストケースを作成する
    /// 
    /// # Arguments
    /// 
    /// * `input` - テストの入力データ
    /// * `expected_output` - 期待される出力
    /// * `timeout_secs` - タイムアウト時間（秒）
    /// * `memory_limit_mb` - メモリ制限（MB単位）
    #[must_use]
    pub const fn with_limits(
        input: String,
        expected_output: String,
        timeout_secs: u64,
        memory_limit_mb: u64,
    ) -> Self {
        Self {
            input,
            expected_output,
            timeout_secs: Some(timeout_secs),
            memory_limit_mb: Some(memory_limit_mb),
        }
    }
}

/// テストスイートを表す構造体
#[derive(Debug, Clone)]
pub struct Suite {
    pub cases: Vec<Case>,
}

/// テスト結果を表す構造体
#[derive(Debug, Clone)]
pub struct TestResult {
    pub passed: bool,
    pub message: String,
} 