#[cfg(test)]
mod docker_tests {
    use std::process::Command;
    use cph::Language;

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
} 