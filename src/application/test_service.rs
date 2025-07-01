use std::path::{Path, PathBuf};
use crate::domain::test_case::{ProblemDirectory, TestCase, TestResult};
use crate::errors::AppResult;
use crate::interfaces::file_system::FileSystem;
use crate::interfaces::test_runner::TestRunner;
use std::sync::Arc;
use tracing::{info, error};

pub struct TestService {
    file_system: Arc<dyn FileSystem>,
    test_runner: Arc<dyn TestRunner>,
}

impl TestService {
    pub fn new(
        file_system: Arc<dyn FileSystem>,
        test_runner: Arc<dyn TestRunner>,
    ) -> Self {
        Self {
            file_system,
            test_runner,
        }
    }

    pub async fn run_tests(&self, path: Option<PathBuf>) -> AppResult<Vec<TestResult>> {
        let problem_dir = self.find_problem_directory(path).await?;
        info!("Running tests in: {:?}", problem_dir.path);
        
        let solution_path = self.find_solution_file(&problem_dir.path).await?;
        info!("Found solution file: {:?}", solution_path);
        
        let test_cases = self.load_test_cases(&problem_dir.path).await?;
        if test_cases.is_empty() {
            error!("No test cases found in directory");
            return Err(crate::errors::AppError::Validation(
                "No test cases found in directory".to_string()
            ));
        }
        
        self.test_runner.compile_solution(&solution_path).await?;
        
        let mut results = Vec::new();
        for test_case in test_cases {
            let result = self.test_runner.run_test(&test_case, &solution_path).await?;
            results.push(result);
        }
        
        Ok(results)
    }
    
    async fn find_problem_directory(&self, path: Option<PathBuf>) -> AppResult<ProblemDirectory> {
        let base_path = path.unwrap_or_else(|| PathBuf::from("."));
        
        if self.file_system.exists(&base_path.join("sample")).await? {
            Ok(ProblemDirectory::new(base_path))
        } else {
            Err(crate::errors::AppError::Validation(
                "Not a valid problem directory (missing 'sample' subdirectory)".to_string()
            ))
        }
    }
    
    async fn find_solution_file(&self, problem_dir: &Path) -> AppResult<PathBuf> {
        let extensions = ["rs", "cpp", "py", "java", "go", "js"];
        
        for ext in &extensions {
            let solution_path = problem_dir.join(format!("main.{}", ext));
            if self.file_system.exists(&solution_path).await? {
                return Ok(solution_path);
            }
        }
        
        Err(crate::errors::AppError::NotFound(
            "No solution file found (looking for main.* with common extensions)".to_string()
        ))
    }
    
    async fn load_test_cases(&self, problem_dir: &Path) -> AppResult<Vec<TestCase>> {
        let sample_dir = problem_dir.join("sample");
        let mut test_cases = Vec::new();
        
        let entries = self.file_system.list_dir(&sample_dir).await?;
        let mut input_files = Vec::new();
        
        for entry in entries {
            if entry.to_string_lossy().ends_with(".in") {
                input_files.push(entry);
            }
        }
        
        input_files.sort();
        
        for input_file in input_files {
            let base_name = input_file.file_stem()
                .ok_or_else(|| crate::errors::AppError::Validation("Invalid input file name".to_string()))?
                .to_string_lossy();
            
            let output_file = sample_dir.join(format!("{}.out", base_name));
            
            if self.file_system.exists(&output_file).await? {
                let input = self.file_system.read(&input_file).await?;
                let expected_output = self.file_system.read(&output_file).await?;
                
                test_cases.push(TestCase {
                    name: base_name.to_string(),
                    input,
                    expected_output,
                });
            }
        }
        
        Ok(test_cases)
    }
}