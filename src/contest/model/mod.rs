pub mod state;

use std::path::PathBuf;
use anyhow::Result;
use crate::fs::manager::Manager;

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
    /// Creates a new Contest instance
    #[must_use = "この関数は新しいContestインスタンスを返します"]
    pub fn new(site: String, contest_id: String, problem_id: String, language: String, url: String) -> Self {
        Self {
            id: format!("{site}_{problem_id}"),
            name: format!("{contest_id} - {problem_id}"),
            url,
            site,
            contest_id,
            problem_id,
            language,
        }
    }

    /// Creates a workspace directory structure for the contest
    /// 
    /// # Errors
    /// 
    /// Returns an error if:
    /// - Failed to create directories
    /// - Failed to begin or commit transaction
    #[must_use = "この関数は新しいManagerインスタンスを返します"]
    pub fn create_workspace(&self, manager: Manager) -> Result<Manager> {
        let workspace_path = PathBuf::from(&self.id);
        
        manager.begin_transaction()?
            .create_dir(&workspace_path)?
            .create_dir(workspace_path.join("src"))?
            .create_dir(workspace_path.join("test"))?
            .commit()
    }

    /// Saves the template code to the workspace
    /// 
    /// # Errors
    /// 
    /// Returns an error if:
    /// - Failed to write template file
    /// - Failed to begin or commit transaction
    #[must_use = "この関数は新しいManagerインスタンスを返します"]
    pub fn save_template(&self, manager: Manager, template: &str) -> Result<Manager> {
        let source_path = PathBuf::from(&self.id).join("src").join("main.rs");
        
        manager.begin_transaction()?
            .write_file(&source_path, template)?
            .commit()
    }

    /// Saves a test case to the workspace
    /// 
    /// # Errors
    /// 
    /// Returns an error if:
    /// - Failed to write input/expected files
    /// - Failed to begin or commit transaction
    #[must_use = "この関数は新しいManagerインスタンスを返します"]
    pub fn save_test_case(&self, manager: Manager, test_case: &TestCase, index: usize) -> Result<Manager> {
        let test_dir = PathBuf::from(&self.id).join("test");
        let input_path = test_dir.join(format!("input{index}.txt"));
        let expected_path = test_dir.join(format!("expected{index}.txt"));

        manager.begin_transaction()?
            .write_file(&input_path, &test_case.input)?
            .write_file(&expected_path, &test_case.expected)?
            .commit()
    }

    /// Cleans up the workspace by deleting all files
    /// 
    /// # Errors
    /// 
    /// Returns an error if:
    /// - Failed to delete workspace directory
    /// - Failed to begin or commit transaction
    #[must_use = "この関数は新しいManagerインスタンスを返します"]
    pub fn cleanup(&self, manager: Manager) -> Result<Manager> {
        let workspace_path = PathBuf::from(&self.id);
        
        manager.begin_transaction()?
            .delete_file(&workspace_path)?
            .commit()
    }

    /// テストディレクトリのパスを取得します
    /// 
    /// # Returns
    /// * `Result<PathBuf>` - テストディレクトリのパス
    /// 
    /// # Errors
    /// - テストディレクトリが存在しない場合
    pub fn get_test_dir(&self) -> Result<PathBuf> {
        let path = PathBuf::from(&self.id).join("test");
        if !path.exists() {
            return Err(anyhow::anyhow!(
                "テストディレクトリが見つかりません: {}", path.display()
            ));
        }
        Ok(path)
    }

    /// ソースファイルのパスを取得します
    /// 
    /// # Returns
    /// * `Result<PathBuf>` - ソースファイルのパス
    /// 
    /// # Errors
    /// - ソースファイルが存在しない場合
    pub fn get_source_file(&self) -> Result<PathBuf> {
        let path = PathBuf::from(&self.id).join("src").join("main.rs");
        if !path.exists() {
            return Err(anyhow::anyhow!(
                "ソースファイルが見つかりません: {}", path.display()
            ));
        }
        Ok(path)
    }
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct TestCase {
    pub input: String,
    pub expected: String,
    pub path: String,
}

impl TestCase {
    #[must_use]
    pub const fn new(input: String, expected: String) -> Self {
        Self {
            input,
            expected,
            path: String::new(),
        }
    }
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum Command {
    Login,
    Config {
        site: Option<String>,
        contest_id: Option<String>,
        problem_id: Option<String>,
        language: Option<String>,
    },
    Open,
    Test {
        test_number: Option<usize>,
    },
    Submit,
}

#[derive(Debug, Clone)]
pub struct CommandContext {
    pub command: Command,
    pub contest: Option<Contest>,
}

impl CommandContext {
    #[must_use]
    pub const fn new(command: Command) -> Self {
        Self {
            command,
            contest: None,
        }
    }

    #[must_use]
    pub const fn with_contest(command: Command, contest: Contest) -> Self {
        Self {
            command,
            contest: Some(contest),
        }
    }
} 