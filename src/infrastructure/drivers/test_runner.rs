use async_trait::async_trait;
use std::path::Path;
use std::sync::Arc;
use std::time::{Duration, Instant};
use tokio::time::sleep;
use crate::domain::test_case::{TestCase, TestResult, TestStatus};
use crate::errors::AppResult;
use crate::interfaces::shell::Shell;
use crate::interfaces::test_runner::TestRunner;
use tracing::{debug, error};

pub struct LocalTestRunner {
    shell: Arc<dyn Shell>,
}

impl LocalTestRunner {
    pub fn new(shell: Arc<dyn Shell>) -> Self {
        Self { shell }
    }
    
    fn get_compile_command(&self, solution_path: &Path) -> Option<String> {
        let extension = solution_path.extension()?.to_str()?;
        let parent = solution_path.parent()?;
        let output_path = parent.join("solution");
        
        match extension {
            "rs" => Some(format!("rustc {} -o {}", solution_path.display(), output_path.display())),
            "cpp" => Some(format!("g++ -std=c++17 -O2 {} -o {}", solution_path.display(), output_path.display())),
            "py" => None, // Python doesn't need compilation
            "java" => Some(format!("javac {}", solution_path.display())),
            "go" => Some(format!("go build -o {} {}", output_path.display(), solution_path.display())),
            "js" => None, // JavaScript doesn't need compilation
            _ => None,
        }
    }
    
    fn get_run_command(&self, solution_path: &Path) -> Option<String> {
        let extension = solution_path.extension()?.to_str()?;
        let parent = solution_path.parent()?;
        let executable_path = parent.join("solution");
        
        match extension {
            "rs" | "cpp" | "go" => Some(executable_path.display().to_string()),
            "py" => Some(format!("python3 {}", solution_path.display())),
            "java" => {
                let class_name = solution_path.file_stem()?.to_str()?;
                Some(format!("java {}", class_name))
            },
            "js" => Some(format!("node {}", solution_path.display())),
            _ => None,
        }
    }
}

#[async_trait]
impl TestRunner for LocalTestRunner {
    async fn compile_solution(&self, solution_path: &Path) -> AppResult<()> {
        if let Some(compile_cmd) = self.get_compile_command(solution_path) {
            debug!("Compiling with: {}", compile_cmd);
            
            let cwd = solution_path.parent();
            let output = self.shell.execute_with_cwd(&compile_cmd, cwd).await?;
            
            if !output.status.success() {
                error!("Compilation failed: {}", output.stderr);
                return Err(crate::errors::AppError::Execution(
                    format!("Compilation failed: {}", output.stderr)
                ));
            }
            
            // Small delay to ensure the compiled file is fully written and not locked
            sleep(Duration::from_millis(50)).await;
        }
        
        Ok(())
    }
    
    async fn run_test(&self, test_case: &TestCase, solution_path: &Path) -> AppResult<TestResult> {
        let run_cmd = self.get_run_command(solution_path)
            .ok_or_else(|| crate::errors::AppError::Validation(
                "Unsupported file extension".to_string()
            ))?;
        
        debug!("Running test '{}' with command: {}", test_case.name, run_cmd);
        
        let start_time = Instant::now();
        let cwd = solution_path.parent();
        let output = self.shell.execute_with_input_and_cwd(&run_cmd, &test_case.input, cwd).await?;
        let execution_time_ms = start_time.elapsed().as_millis() as u64;
        
        let actual_output = output.stdout.trim_end().to_string();
        let expected_output = test_case.expected_output.trim_end().to_string();
        
        let status = if !output.status.success() {
            TestStatus::RuntimeError {
                message: output.stderr.clone(),
            }
        } else if actual_output == expected_output {
            TestStatus::Passed
        } else {
            TestStatus::Failed {
                reason: format!(
                    "Expected:\n{}\n\nActual:\n{}",
                    expected_output,
                    actual_output
                ),
            }
        };
        
        Ok(TestResult {
            test_case: test_case.clone(),
            actual_output,
            status,
            execution_time_ms,
        })
    }
}