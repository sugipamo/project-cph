use assert_cmd::Command;
use predicates::prelude::*;
use std::fs;
use tempfile::TempDir;

#[test]
fn test_invalid_language() {
    let mut cmd = Command::cargo_bin("cph").unwrap();
    cmd.args(["abc300", "invalid", "open", "a"])
        .assert()
        .failure()
        .stderr(predicate::str::contains("Invalid language"));
}

#[test]
fn test_invalid_command() {
    let mut cmd = Command::cargo_bin("cph").unwrap();
    cmd.args(["abc300", "rust", "invalid", "a"])
        .assert()
        .failure()
        .stderr(predicate::str::contains("Invalid command"));
}

#[test]
fn test_open_command_with_template() {
    let temp_dir = TempDir::new().unwrap();
    let workspace = temp_dir.path().join("workspace");
    let abc_dir = workspace.join("abc").join("abc300");
    let template_dir = abc_dir.join("template");
    
    // Create template directory and file
    fs::create_dir_all(&template_dir).unwrap();
    fs::write(template_dir.join("main.rs"), "// Template content").unwrap();
    
    let mut cmd = Command::cargo_bin("cph").unwrap();
    cmd.current_dir(&temp_dir)
        .args(["abc300", "rust", "open", "a"])
        .assert()
        .success();
    
    // Check if problem file was created
    let problem_file = abc_dir.join("a.rs");
    assert!(problem_file.exists());
    assert_eq!(fs::read_to_string(problem_file).unwrap(), "// Template content");
}

#[test]
fn test_open_command_without_template() {
    let temp_dir = TempDir::new().unwrap();
    
    let mut cmd = Command::cargo_bin("cph").unwrap();
    cmd.current_dir(&temp_dir)
        .args(["abc300", "rust", "open", "a"])
        .assert()
        .success();
    
    // Check if problem file was created with default content
    let problem_file = temp_dir.path().join("workspace/abc/abc300/a.rs");
    assert!(problem_file.exists());
    assert_eq!(fs::read_to_string(problem_file).unwrap(), "fn main() {\n    \n}\n");
}

#[test]
fn test_abbreviated_commands() {
    let temp_dir = TempDir::new().unwrap();
    let workspace = temp_dir.path().join("workspace");
    let abc_dir = workspace.join("abc").join("abc300");
    let template_dir = abc_dir.join("template");
    
    // Create template directory and file
    fs::create_dir_all(&template_dir).unwrap();
    fs::write(template_dir.join("main.rs"), "// Template content").unwrap();
    
    let mut cmd = Command::cargo_bin("cph").unwrap();
    cmd.current_dir(&temp_dir)
        .args(["abc300", "r", "o", "a"])
        .assert()
        .success();
    
    // Check if problem file was created
    assert!(abc_dir.join("a.rs").exists());
}

#[test]
fn test_test_command_no_test_dir() {
    let temp_dir = TempDir::new().unwrap();
    let workspace = temp_dir.path().join("workspace");
    let abc_dir = workspace.join("abc").join("abc300");
    
    // Create problem file
    fs::create_dir_all(&abc_dir).unwrap();
    fs::write(
        abc_dir.join("a.rs"),
        "fn main() { println!(\"Hello\"); }",
    ).unwrap();
    
    let mut cmd = Command::cargo_bin("cph").unwrap();
    cmd.current_dir(&temp_dir)
        .args(["abc300", "rust", "test", "a"])
        .assert()
        .failure()
        .stderr(predicate::str::contains("Test directory not found"));
}

#[test]
fn test_test_command_with_sample() {
    let temp_dir = TempDir::new().unwrap();
    let workspace = temp_dir.path().join("workspace");
    let abc_dir = workspace.join("abc").join("abc300");
    let test_dir = abc_dir.join("test");
    
    // Create problem file
    fs::create_dir_all(&abc_dir).unwrap();
    fs::write(
        abc_dir.join("a.rs"),
        "fn main() { println!(\"Hello\"); }",
    ).unwrap();
    
    // Create test cases
    fs::create_dir_all(&test_dir).unwrap();
    fs::write(test_dir.join("sample-1.in"), "").unwrap();
    fs::write(test_dir.join("sample-1.out"), "Hello\n").unwrap();
    
    let mut cmd = Command::cargo_bin("cph").unwrap();
    cmd.current_dir(&temp_dir)
        .args(["abc300", "rust", "test", "a"])
        .assert()
        .success();
}

#[test]
fn test_test_command_with_failing_test() {
    let temp_dir = TempDir::new().unwrap();
    let workspace = temp_dir.path().join("workspace");
    let abc_dir = workspace.join("abc").join("abc300");
    let test_dir = abc_dir.join("test");
    
    // Create problem file
    fs::create_dir_all(&abc_dir).unwrap();
    fs::write(
        abc_dir.join("a.rs"),
        "fn main() { println!(\"Wrong\"); }",
    ).unwrap();
    
    // Create test cases
    fs::create_dir_all(&test_dir).unwrap();
    fs::write(test_dir.join("sample-1.in"), "").unwrap();
    fs::write(test_dir.join("sample-1.out"), "Hello\n").unwrap();
    
    let mut cmd = Command::cargo_bin("cph").unwrap();
    cmd.current_dir(&temp_dir)
        .args(["abc300", "rust", "test", "a"])
        .assert()
        .failure()
        .stderr(predicate::str::contains("Some tests failed"));
}

#[test]
fn test_test_command_with_timeout() {
    let temp_dir = TempDir::new().unwrap();
    let workspace = temp_dir.path().join("workspace");
    let abc_dir = workspace.join("abc").join("abc300");
    let test_dir = abc_dir.join("test");
    
    // Create problem file with infinite loop
    fs::create_dir_all(&abc_dir).unwrap();
    fs::write(
        abc_dir.join("a.rs"),
        "fn main() { loop {} }",
    ).unwrap();
    
    // Create test cases
    fs::create_dir_all(&test_dir).unwrap();
    fs::write(test_dir.join("sample-1.in"), "").unwrap();
    fs::write(test_dir.join("sample-1.out"), "Hello\n").unwrap();
    
    let mut cmd = Command::cargo_bin("cph").unwrap();
    cmd.current_dir(&temp_dir)
        .args(["abc300", "rust", "test", "a"])
        .assert()
        .failure()
        .stdout(predicate::str::contains("timed out"));
} 