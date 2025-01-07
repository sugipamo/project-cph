pub mod state;

use std::path::PathBuf;
use crate::error::Result;
use crate::fs::manager::FileManager;

#[derive(Debug, Clone)]
pub struct Contest {
    pub id: String,
    pub name: String,
    pub url: String,
    pub site: String,
    pub contest_id: String,
    pub problem_id: String,
    pub language: String,
}

impl Contest {
    pub fn new(site: String, contest_id: String, problem_id: String, language: String, url: String) -> Self {
        Self {
            id: format!("{}_{}", site, problem_id),
            name: format!("{} - {}", contest_id, problem_id),
            url,
            site,
            contest_id,
            problem_id,
            language,
        }
    }

    pub fn create_workspace(&self, manager: FileManager) -> Result<FileManager> {
        let workspace_path = PathBuf::from(&self.id);
        
        manager.begin_transaction()?
            .create_dir(&workspace_path)?
            .create_dir(workspace_path.join("src"))?
            .create_dir(workspace_path.join("test"))?
            .commit()
    }

    pub fn save_template(&self, manager: FileManager, template: &str) -> Result<FileManager> {
        let source_path = PathBuf::from(&self.id).join("src").join("main.rs");
        
        manager.begin_transaction()?
            .write_file(&source_path, template)?
            .commit()
    }

    pub fn save_test_case(&self, manager: FileManager, test_case: &TestCase, index: usize) -> Result<FileManager> {
        let test_dir = PathBuf::from(&self.id).join("test");
        let input_path = test_dir.join(format!("input{}.txt", index));
        let expected_path = test_dir.join(format!("expected{}.txt", index));

        manager.begin_transaction()?
            .write_file(&input_path, &test_case.input)?
            .write_file(&expected_path, &test_case.expected)?
            .commit()
    }

    pub fn cleanup(&self, manager: FileManager) -> Result<FileManager> {
        let workspace_path = PathBuf::from(&self.id);
        
        manager.begin_transaction()?
            .delete_file(&workspace_path)?
            .commit()
    }
}

#[derive(Debug, Clone)]
pub struct TestCase {
    pub input: String,
    pub expected: String,
    pub path: String,
}

impl TestCase {
    pub fn new(input: String, expected: String) -> Self {
        Self {
            input,
            expected,
            path: String::new(),
        }
    }
} 