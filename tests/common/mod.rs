pub mod test_helpers {
    use std::path::PathBuf;
    use tempfile::TempDir;

    pub struct TestEnvironment {
        _temp_dir: TempDir,
        pub work_dir: PathBuf,
    }

    impl TestEnvironment {
        pub fn new() -> Self {
            let temp_dir = TempDir::new().unwrap();
            let work_dir = temp_dir.path().join("workspace");
            std::fs::create_dir_all(&work_dir).unwrap();
            
            Self {
                _temp_dir: temp_dir,
                work_dir,
            }
        }

        pub fn create_file(&self, relative_path: &str, content: &str) -> PathBuf {
            let file_path = self.work_dir.join(relative_path);
            if let Some(parent) = file_path.parent() {
                std::fs::create_dir_all(parent).unwrap();
            }
            std::fs::write(&file_path, content).unwrap();
            file_path
        }

        pub fn read_file(&self, relative_path: &str) -> String {
            let file_path = self.work_dir.join(relative_path);
            std::fs::read_to_string(file_path).unwrap()
        }

        pub fn file_exists(&self, relative_path: &str) -> bool {
            self.work_dir.join(relative_path).exists()
        }
    }
}

pub mod fixtures {
    pub const SAMPLE_CONFIG: &str = r#"
[app]
name = "test-app"
version = "0.1.0"

[docker]
enabled = true
registry = "localhost:5000"
"#;

    #[allow(dead_code)]
    pub const SAMPLE_WORKFLOW: &str = r#"
name: test-workflow
steps:
  - name: build
    command: cargo build
  - name: test
    command: cargo test
"#;
}

// Mock implementations will be added as needed