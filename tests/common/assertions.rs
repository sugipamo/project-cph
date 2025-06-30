use predicates::prelude::*;

pub trait OutputAssertions {
    fn assert_stdout_contains(&self, expected: &str);
    fn assert_stderr_is_empty(&self);
    fn assert_exit_code(&self, code: i32);
}

#[derive(Debug)]
pub struct CommandOutput {
    pub stdout: String,
    pub stderr: String,
    pub exit_code: i32,
}

impl OutputAssertions for CommandOutput {
    fn assert_stdout_contains(&self, expected: &str) {
        let predicate = predicate::str::contains(expected);
        assert!(
            predicate.eval(&self.stdout),
            "stdout does not contain expected string.\nExpected: {}\nActual stdout: {}",
            expected,
            self.stdout
        );
    }

    fn assert_stderr_is_empty(&self) {
        assert!(
            self.stderr.is_empty(),
            "stderr is not empty: {}",
            self.stderr
        );
    }

    fn assert_exit_code(&self, code: i32) {
        assert_eq!(
            self.exit_code, code,
            "exit code mismatch. Expected: {}, Actual: {}",
            code, self.exit_code
        );
    }
}

#[allow(dead_code)]
pub fn assert_file_contains(path: &std::path::Path, expected: &str) {
    let content = std::fs::read_to_string(path)
        .unwrap_or_else(|e| panic!("Failed to read file {:?}: {}", path, e));
    
    assert!(
        content.contains(expected),
        "File {:?} does not contain expected string.\nExpected: {}\nActual content: {}",
        path,
        expected,
        content
    );
}

#[allow(dead_code)]
pub fn assert_dir_exists(path: &std::path::Path) {
    assert!(
        path.exists() && path.is_dir(),
        "Directory {:?} does not exist",
        path
    );
}

#[allow(dead_code)]
pub fn assert_file_exists(path: &std::path::Path) {
    assert!(
        path.exists() && path.is_file(),
        "File {:?} does not exist",
        path
    );
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_command_output_assertions() {
        let output = CommandOutput {
            stdout: "Hello, World!".to_string(),
            stderr: String::new(),
            exit_code: 0,
        };

        output.assert_stdout_contains("Hello");
        output.assert_stderr_is_empty();
        output.assert_exit_code(0);
    }

    #[test]
    #[should_panic(expected = "stdout does not contain expected string")]
    fn test_stdout_assertion_fails() {
        let output = CommandOutput {
            stdout: "Hello".to_string(),
            stderr: String::new(),
            exit_code: 0,
        };

        output.assert_stdout_contains("Goodbye");
    }
}