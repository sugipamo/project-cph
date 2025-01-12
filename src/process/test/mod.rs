use std::path::PathBuf;

pub mod runner;

#[derive(Debug, Clone)]
pub struct TestCase {
    pub input: String,
    pub expected_output: String,
    pub timeout_secs: u64,
    pub memory_limit_mb: u64,
}

impl TestCase {
    pub fn new(input: String, expected_output: String) -> Self {
        Self {
            input,
            expected_output,
            timeout_secs: 2,
            memory_limit_mb: 256,
        }
    }

    pub fn with_limits(
        input: String,
        expected_output: String,
        timeout_secs: u64,
        memory_limit_mb: u64,
    ) -> Self {
        Self {
            input,
            expected_output,
            timeout_secs,
            memory_limit_mb,
        }
    }
}

#[derive(Debug)]
pub struct TestSuite {
    pub source_file: PathBuf,
    pub test_cases: Vec<TestCase>,
    pub working_dir: Option<PathBuf>,
}

#[derive(Debug)]
pub struct TestResult {
    pub success: bool,
    pub execution_time_ms: u64,
    pub error: Option<String>,
} 