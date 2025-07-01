use std::path::PathBuf;

#[derive(Debug, Clone, PartialEq)]
pub struct TestCase {
    pub name: String,
    pub input: String,
    pub expected_output: String,
}

#[derive(Debug, Clone)]
pub struct TestResult {
    pub test_case: TestCase,
    pub actual_output: String,
    pub status: TestStatus,
    pub execution_time_ms: u64,
}

#[derive(Debug, Clone, PartialEq)]
pub enum TestStatus {
    Passed,
    Failed { reason: String },
    RuntimeError { message: String },
    CompilationError { message: String },
    TimeLimitExceeded,
}

#[derive(Debug, Clone)]
pub struct ProblemDirectory {
    pub path: PathBuf,
    pub sample_tests: Vec<TestCase>,
}

impl ProblemDirectory {
    pub fn new(path: PathBuf) -> Self {
        Self {
            path,
            sample_tests: Vec::new(),
        }
    }

    pub fn add_test_case(&mut self, test_case: TestCase) {
        self.sample_tests.push(test_case);
    }
}