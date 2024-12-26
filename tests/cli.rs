use assert_cmd::Command;
use predicates::prelude::*;
use std::fs;
use tempfile::TempDir;
use cph::docker::DockerConfig;

struct TestContext {
    temp_dir: TempDir,
    abc_dir: std::path::PathBuf,
}

impl TestContext {
    fn new() -> Self {
        let temp_dir = TempDir::new().unwrap();
        let abc_dir = temp_dir.path().join("workspace/abc/abc300");
        
        fs::create_dir_all(&abc_dir).unwrap();
        
        Self {
            temp_dir,
            abc_dir,
        }
    }

    fn create_template(&self, content: &str) {
        let template_dir = self.abc_dir.join("template");
        fs::create_dir_all(&template_dir).unwrap();
        fs::write(template_dir.join("main.rs"), content).unwrap();
    }

    fn run_in_docker(&self, args: &[&str], language: &str) -> assert_cmd::assert::Assert {
        let image = DockerConfig::get().get_image(language);

        // バイナリをコピー
        let binary_path = assert_cmd::cargo::cargo_bin("cph");
        fs::copy(&binary_path, self.temp_dir.path().join("cph")).unwrap();

        Command::new("docker")
            .args([
                "run",
                "--rm",
                "--memory",
                &DockerConfig::get().memory_limit,
                "--memory-swap",
                &DockerConfig::get().memory_limit,
                "-v",
                &format!("{}:/workspace", self.temp_dir.path().display()),
                "-w",
                "/workspace",
                &image,
                "./cph",
            ])
            .args(args)
            .assert()
    }
}

// 基本的なコマンドライン引数のテストはDocker外で実行
#[test]
fn test_invalid_language() {
    Command::cargo_bin("cph")
        .unwrap()
        .args(["abc300", "invalid", "open", "a"])
        .assert()
        .failure()
        .stderr(predicate::str::contains("Invalid language"));
}

#[test]
fn test_invalid_command() {
    Command::cargo_bin("cph")
        .unwrap()
        .args(["abc300", "rust", "invalid", "a"])
        .assert()
        .failure()
        .stderr(predicate::str::contains("Invalid command"));
}

// 以下のテストはDocker環境で実行
#[test]
fn test_open_command_with_template() {
    let ctx = TestContext::new();
    ctx.create_template("// Template content");
    
    ctx.run_in_docker(&["abc300", "rust", "open", "a"], "rust")
        .success();
    
    let problem_file = ctx.abc_dir.join("a.rs");
    assert!(problem_file.exists());
    assert_eq!(fs::read_to_string(problem_file).unwrap(), "// Template content");
}

#[test]
fn test_open_command_without_template() {
    let ctx = TestContext::new();
    
    ctx.run_in_docker(&["abc300", "rust", "open", "a"], "rust")
        .success();
    
    let problem_file = ctx.abc_dir.join("a.rs");
    assert!(problem_file.exists());
    assert_eq!(fs::read_to_string(problem_file).unwrap(), "fn main() {\n    \n}\n");
}

#[test]
fn test_generate_command_create_gen_file() {
    let ctx = TestContext::new();
    
    ctx.run_in_docker(&["abc300", "rust", "generate", "a"], "rust")
        .success()
        .stdout(predicate::str::contains("Created generator file"));
    
    let gen_file = ctx.abc_dir.join("a_gen.rs");
    assert!(gen_file.exists());
}

#[test]
fn test_generate_command_execute_gen() {
    let ctx = TestContext::new();
    
    // First call to create generator
    ctx.run_in_docker(&["abc300", "rust", "generate", "a"], "rust")
        .success();
    
    // Modify generator to output specific test case
    let gen_file = ctx.abc_dir.join("a_gen.rs");
    fs::write(&gen_file, r#"
fn generate_case() -> (String, String) {
    ("1 2\n".to_string(), "3\n".to_string())
}

fn main() {
    let (input, output) = generate_case();
    println!("{}", input);
    eprintln!("{}", output);
}
"#).unwrap();
    
    // Second call to generate test case
    ctx.run_in_docker(&["abc300", "rust", "generate", "a"], "rust")
        .success();
    
    let test_dir = ctx.abc_dir.join("test");
    let input_file = test_dir.join("custom-1.in");
    let output_file = test_dir.join("custom-1.out");
    
    assert!(input_file.exists());
    assert!(output_file.exists());
    assert_eq!(fs::read_to_string(input_file).unwrap(), "1 2\n");
    assert_eq!(fs::read_to_string(output_file).unwrap(), "3\n");
}

#[test]
fn test_test_command_with_custom_case() {
    let ctx = TestContext::new();
    
    // Create problem file
    fs::write(
        ctx.abc_dir.join("a.rs"),
        r#"
fn main() {
    let mut line = String::new();
    std::io::stdin().read_line(&mut line).unwrap();
    let nums: Vec<i32> = line
        .split_whitespace()
        .map(|s| s.parse().unwrap())
        .collect();
    println!("{}", nums[0] + nums[1]);
}
"#,
    ).unwrap();
    
    // Create test cases
    let test_dir = ctx.abc_dir.join("test");
    fs::write(test_dir.join("custom-1.in"), "1 2\n").unwrap();
    fs::write(test_dir.join("custom-1.out"), "3\n").unwrap();
    
    ctx.run_in_docker(&["abc300", "rust", "test", "a"], "rust")
        .success();
}

#[test]
fn test_test_command_with_failing_test() {
    let ctx = TestContext::new();
    
    // Create problem file with wrong output
    fs::write(
        ctx.abc_dir.join("a.rs"),
        "fn main() { println!(\"Wrong\"); }",
    ).unwrap();
    
    // Create test cases
    let test_dir = ctx.abc_dir.join("test");
    fs::write(test_dir.join("sample-1.in"), "").unwrap();
    fs::write(test_dir.join("sample-1.out"), "Correct\n").unwrap();
    
    ctx.run_in_docker(&["abc300", "rust", "test", "a"], "rust")
        .failure()
        .stderr(predicate::str::contains("Some tests failed"));
}

#[test]
fn test_pypy_support() {
    let ctx = TestContext::new();
    
    ctx.run_in_docker(&["abc300", "pypy", "open", "a"], "pypy")
        .success();
    
    let problem_file = ctx.abc_dir.join("a.py");
    assert!(problem_file.exists());
    assert!(fs::read_to_string(problem_file).unwrap().contains("def main():"));
}

#[test]
fn test_test_command_timeout() {
    let ctx = TestContext::new();
    
    // Create problem file with infinite loop
    fs::write(
        ctx.abc_dir.join("a.rs"),
        "fn main() { loop {} }",
    ).unwrap();
    
    // Create test cases
    let test_dir = ctx.abc_dir.join("test");
    fs::write(test_dir.join("sample-1.in"), "").unwrap();
    fs::write(test_dir.join("sample-1.out"), "Hello\n").unwrap();
    
    ctx.run_in_docker(&["abc300", "rust", "test", "a"], "rust")
        .failure()
        .stdout(predicate::str::contains("timed out"));
} 