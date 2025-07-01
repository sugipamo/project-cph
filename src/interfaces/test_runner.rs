use async_trait::async_trait;
use crate::domain::test_case::{TestCase, TestResult};
use crate::errors::AppResult;
use std::path::Path;

#[async_trait]
pub trait TestRunner: Send + Sync {
    async fn run_test(&self, test_case: &TestCase, solution_path: &Path) -> AppResult<TestResult>;
    async fn compile_solution(&self, solution_path: &Path) -> AppResult<()>;
}