#[cfg(test)]
mod docker_tests {
    use std::process::Command;
    use cph::Language;
    use std::fs;

    struct DockerTest {
        language: Language,
        version_cmd: &'static [&'static str],
        version_output_contains: &'static str,
    }

    impl DockerTest {
        fn new(language: Language, version_cmd: &'static [&'static str], version_output_contains: &'static str) -> Self {
            Self {
                language,
                version_cmd,
                version_output_contains,
            }
        }

        fn image(&self) -> String {
            self.language.docker_image().to_string()
        }

        fn run_command(&self, cmd: &[&str]) -> std::io::Result<std::process::Output> {
            Command::new("docker")
                .args(["run", "--rm"])
                .arg(self.image())
                .args(cmd)
                .output()
        }

        fn run_command_with_memory_limit(&self, cmd: &[&str], memory_limit: &str) -> std::io::Result<std::process::Output> {
            Command::new("docker")
                .args([
                    "run",
                    "--rm",
                    "--memory",
                    memory_limit,
                    "--memory-swap",
                    memory_limit,
                ])
                .arg(self.image())
                .args(cmd)
                .output()
        }

        fn test_version_command(&self) {
            let output = self.run_command(self.version_cmd)
                .unwrap_or_else(|_| panic!("Failed to execute command in {} container", self.image()));
            
            assert!(output.status.success(), "Command failed in {} container", self.image());
            let output_str = String::from_utf8_lossy(&output.stdout);
            assert!(
                output_str.contains(self.version_output_contains), 
                "Unexpected version output for {}", self.image()
            );
        }

        fn test_memory_limit(&self, script: &str) {
            match self.language {
                Language::Rust => {
                    // Rustの場合は一時ファイルを作成してコンパイル
                    let temp_dir = tempfile::tempdir().unwrap();
                    let source_path = temp_dir.path().join("main.rs");
                    fs::write(&source_path, script).unwrap();
                    
                    // コンパイル（メモリ制限なし）
                    let output = self.run_command(&[
                        "rustc",
                        "/workspace/main.rs",
                        "-o",
                        "/workspace/main"
                    ]).unwrap();
                    assert!(output.status.success(), "Compilation failed for Rust");

                    // 実行（メモリ制限あり）
                    let output = self.run_command_with_memory_limit(
                        &["/workspace/main"],
                        if script.contains("10_000_000") { "1m" } else { "10m" }
                    ).unwrap();
                    
                    // メモリ制限を超えた場合はエラーになるはず
                    if script.contains("10_000_000") {
                        assert!(!output.status.success(), "Memory limit test should fail for large allocation");
                    } else {
                        assert!(output.status.success(), "Memory limit test failed for small allocation");
                    }
                },
                Language::PyPy => {
                    // PyPyの場合は直接スクリプトを実行
                    let output = self.run_command_with_memory_limit(
                        &["python", "-c", script],
                        if script.contains("10_000_000") { "1m" } else { "10m" }
                    ).unwrap();

                    if script.contains("10_000_000") {
                        assert!(!output.status.success(), "Memory limit test should fail for large allocation");
                    } else {
                        assert!(output.status.success(), "Memory limit test failed for small allocation");
                    }
                }
            }
        }
    }

    #[test]
    fn test_docker_commands() {
        let tests = [
            DockerTest::new(
                Language::Rust,
                &["rustc", "--version"],
                "rustc"
            ),
            DockerTest::new(
                Language::PyPy,
                &["python", "--version"],
                "Python"
            ),
        ];

        for test in &tests {
            test.test_version_command();
        }
    }

    #[test]
    fn test_memory_limits() {
        let tests = [
            (
                DockerTest::new(
                    Language::Rust,
                    &["rustc", "--version"],
                    "rustc"
                ),
                vec![
                    r#"
                    fn main() {
                        println!("Hello, World!");
                    }
                    "#,
                    r#"
                    fn main() {
                        let v: Vec<i32> = vec![0; 10_000_000];
                        println!("{}", v.len());
                    }
                    "#
                ]
            ),
            (
                DockerTest::new(
                    Language::PyPy,
                    &["python", "--version"],
                    "Python"
                ),
                vec![
                    r#"print('Hello, World!')"#,
                    r#"x = [0] * 10_000_000"#
                ]
            ),
        ];

        for (test, scripts) in &tests {
            for script in scripts {
                test.test_memory_limit(script);
            }
        }
    }
} 