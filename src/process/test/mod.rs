use std::path::PathBuf;
use bytes::Bytes;
use anyhow::Result;

#[derive(Debug)]
pub struct TestCase {
    pub input: String,
    pub expected_output: String,
    pub time_limit: Option<u64>,
    pub memory_limit: Option<u64>,
}

#[derive(Debug)]
pub struct TestResult {
    pub success: bool,
    pub actual_output: Vec<u8>,
    pub execution_time_ms: u64,
    pub memory_usage_mb: Option<u64>,
    pub error: Option<String>,
}

#[derive(Debug)]
pub struct TestSuite {
    pub source_file: PathBuf,
    pub test_cases: Vec<TestCase>,
    pub working_dir: Option<PathBuf>,
}

impl TestCase {
    pub fn new(input: String, expected_output: String) -> Self {
        Self {
            input,
            expected_output,
            time_limit: None,
            memory_limit: None,
        }
    }

    pub fn with_limits(
        input: String,
        expected_output: String,
        time_limit: u64,
        memory_limit: u64,
    ) -> Self {
        Self {
            input,
            expected_output,
            time_limit: Some(time_limit),
            memory_limit: Some(memory_limit),
        }
    }
}

impl TestResult {
    pub fn success(output: Vec<u8>, time_ms: u64, memory_mb: Option<u64>) -> Self {
        Self {
            success: true,
            actual_output: output,
            execution_time_ms: time_ms,
            memory_usage_mb: memory_mb,
            error: None,
        }
    }

    pub fn failure(output: Vec<u8>, time_ms: u64, memory_mb: Option<u64>, error: String) -> Self {
        Self {
            success: false,
            actual_output: output,
            execution_time_ms: time_ms,
            memory_usage_mb: memory_mb,
            error: Some(error),
        }
    }
} 