use std::time::Duration;
use tokio::runtime::Runtime;
use thiserror::Error;

use crate::{Config, Language};
use crate::docker;

#[derive(Debug, Error)]
pub enum TestError {
    #[error("Test execution failed: {0}")]
    Execution(String),
    
    #[error("Test timeout after {0} seconds")]
    Timeout(u64),
    
    #[error("Compilation failed: {0}")]
    CompilationFailed(String),
    
    #[error("Test failed: {reason}")]
    Failed { reason: String },
    
    #[error("Test setup failed: {0}")]
    Setup(String),
}

impl TestError {
    pub fn new(msg: String) -> Self {
        TestError::Execution(msg)
    }
}

#[derive(Debug)]
pub struct TestCase {
    input: String,
    expected: String,
    name: String,
}

impl TestCase {
    fn read_file(path: &std::path::PathBuf, file_type: &str) -> Result<String, crate::Error> {
        std::fs::read_to_string(path)
            .map_err(|e| crate::Error::Test(TestError::Setup(format!("Failed to read {} file: {}", file_type, e))))
    }

    fn from_files(input_path: &std::path::PathBuf, output_path: &std::path::PathBuf) -> Result<Self, crate::Error> {
        let input = Self::read_file(input_path, "input")?;
        let expected = Self::read_file(output_path, "output")?;
        let name = input_path
            .file_stem()
            .and_then(|s| s.to_str())
            .unwrap_or("unknown")
            .to_string();

        Ok(TestCase {
            input,
            expected,
            name,
        })
    }
}

#[derive(Debug)]
struct TestResult {
    name: String,
    status: TestStatus,
    execution_time: Duration,
}

impl TestResult {
    fn new(name: String, status: TestStatus, execution_time: Duration) -> Self {
        Self {
            name,
            status,
            execution_time,
        }
    }

    fn error(name: String, error: TestError, start: std::time::Instant) -> Self {
        Self::new(
            name,
            TestStatus::Error(error),
            start.elapsed(),
        )
    }

    fn display(&self) -> bool {
        match &self.status {
            TestStatus::Pass => {
                println!(
                    "Test {} passed ({:?})",
                    self.name,
                    self.execution_time
                );
                true
            }
            TestStatus::Fail { got, expected } => {
                println!("Test {} failed", self.name);
                println!("Expected:\n{}", expected);
                println!("Got:\n{}", got);
                false
            }
            TestStatus::Error(e) => {
                println!("Test {} error: {}", self.name, e);
                false
            }
            TestStatus::Timeout => {
                println!("Test {} timed out", self.name);
                false
            }
        }
    }
}

#[derive(Debug)]
enum TestStatus {
    Pass,
    Fail { got: String, expected: String },
    Error(TestError),
    Timeout,
}

pub fn run(config: Config) -> Result<(), crate::Error> {
    let test_dir = config.test_dir();
    if !test_dir.exists() {
        return Err(crate::Error::Test(TestError::Setup(format!(
            "Test directory not found: {:?}",
            test_dir
        ))));
    }

    let runtime = Runtime::new()
        .map_err(|e| crate::Error::Test(TestError::Setup(format!("Failed to create runtime: {}", e))))?;

    runtime.block_on(async {
        let mut test_cases = Vec::new();
        
        // Collect sample test cases
        for entry in std::fs::read_dir(&test_dir)? {
            let entry = entry?;
            let path = entry.path();
            if path.extension().and_then(|s| s.to_str()) == Some("in") {
                let input_path = path.clone();
                let output_path = path.with_extension("out");
                if output_path.exists() {
                    if let Ok(test_case) = TestCase::from_files(&input_path, &output_path) {
                        test_cases.push(test_case);
                    }
                }
            }
        }

        // Execute tests in parallel
        let mut handles = Vec::new();
        for test_case in test_cases {
            let config = config.clone();
            handles.push(tokio::spawn(async move {
                execute_test(&config, test_case).await
            }));
        }

        // Collect results
        let mut all_passed = true;
        for handle in handles {
            let result = handle.await.map_err(|e| crate::Error::Test(TestError::Execution(e.to_string())))?;
            if !result.display() {
                all_passed = false;
            }
        }

        if !all_passed {
            return Err(crate::Error::Test(TestError::Failed {
                reason: "Some tests failed".to_string()
            }));
        }

        Ok(())
    })
}

async fn execute_test(config: &Config, test_case: TestCase) -> TestResult {
    let start = std::time::Instant::now();
    
    let result = match config.language {
        Language::Rust => {
            match docker::execute_program("rustc", &[
                config.problem_file().to_str().unwrap(),
                "-o",
                "problem"
            ], None).await {
                Ok((_, stderr)) if !stderr.is_empty() => {
                    return TestResult::error(test_case.name, TestError::CompilationFailed(stderr), start);
                }
                Err(e) => {
                    return TestResult::error(test_case.name, TestError::CompilationFailed(e.to_string()), start);
                }
                Ok(_) => {
                    docker::execute_program("./problem", &[], Some(test_case.input)).await
                }
            }
        }
        Language::PyPy => {
            docker::execute_program("pypy3", &[
                config.problem_file().to_str().unwrap()
            ], Some(test_case.input)).await
        }
    };

    match result {
        Ok((got, _)) => {
            let status = if got.trim() == test_case.expected.trim() {
                TestStatus::Pass
            } else {
                TestStatus::Fail {
                    got,
                    expected: test_case.expected,
                }
            };
            TestResult::new(test_case.name, status, start.elapsed())
        }
        Err(crate::Error::Test(TestError::Timeout(secs))) => {
            TestResult::new(test_case.name, TestStatus::Timeout, Duration::from_secs(secs))
        }
        Err(e) => TestResult::error(test_case.name, TestError::Execution(e.to_string()), start),
    }
} 