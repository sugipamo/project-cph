use std::process::Command;
use tempfile::TempDir;
use std::fs;
use std::path::PathBuf;

fn get_cph_binary() -> PathBuf {
    // First build the project
    let output = Command::new("cargo")
        .args(&["build", "--quiet"])
        .output()
        .expect("Failed to build project");
    
    if !output.status.success() {
        panic!("Failed to build project: {}", String::from_utf8_lossy(&output.stderr));
    }
    
    PathBuf::from("target/debug/cph")
}

#[test]
fn test_command_with_valid_problem() {
    let cph_binary = get_cph_binary();
    let temp_dir = TempDir::new().unwrap();
    let problem_dir = temp_dir.path().join("problem");
    let sample_dir = problem_dir.join("sample");
    
    fs::create_dir_all(&sample_dir).unwrap();
    
    // Create solution file
    fs::write(
        problem_dir.join("main.rs"),
        r#"
use std::io;

fn main() {
    let mut input = String::new();
    io::stdin().read_line(&mut input).unwrap();
    let n: i32 = input.trim().parse().unwrap();
    println!("{}", n + 1);
}
"#
    ).unwrap();
    
    // Create test cases
    fs::write(sample_dir.join("1.in"), "5").unwrap();
    fs::write(sample_dir.join("1.out"), "6").unwrap();
    fs::write(sample_dir.join("2.in"), "10").unwrap();
    fs::write(sample_dir.join("2.out"), "11").unwrap();
    
    // Run test command
    let output = Command::new(&cph_binary)
        .args(&["test", problem_dir.to_str().unwrap()])
        .output()
        .expect("Failed to execute command");
    
    let stdout = String::from_utf8_lossy(&output.stdout);
    let stderr = String::from_utf8_lossy(&output.stderr);
    
    assert!(stdout.contains("✓ Test '1' passed"), "stdout: {}\nstderr: {}", stdout, stderr);
    assert!(stdout.contains("✓ Test '2' passed"));
    assert!(stdout.contains("Passed 2/2 tests"));
    assert!(output.status.success());
}

#[test]
fn test_command_with_failing_test() {
    let cph_binary = get_cph_binary();
    let temp_dir = TempDir::new().unwrap();
    let problem_dir = temp_dir.path().join("problem");
    let sample_dir = problem_dir.join("sample");
    
    fs::create_dir_all(&sample_dir).unwrap();
    
    // Create solution file that gives wrong answer
    fs::write(
        problem_dir.join("main.rs"),
        r#"
fn main() {
    println!("42"); // Always output 42
}
"#
    ).unwrap();
    
    // Create test cases
    fs::write(sample_dir.join("1.in"), "5").unwrap();
    fs::write(sample_dir.join("1.out"), "6").unwrap();
    
    // Run test command
    let output = Command::new(&cph_binary)
        .args(&["test", problem_dir.to_str().unwrap()])
        .output()
        .expect("Failed to execute command");
    
    let stdout = String::from_utf8_lossy(&output.stdout);
    
    assert!(stdout.contains("✗ Test '1' failed"));
    assert!(!output.status.success());
}

#[test]
fn test_command_without_sample_directory() {
    let cph_binary = get_cph_binary();
    let temp_dir = TempDir::new().unwrap();
    let problem_dir = temp_dir.path().join("problem");
    
    fs::create_dir_all(&problem_dir).unwrap();
    
    // Run test command without sample directory
    let output = Command::new(&cph_binary)
        .args(&["test", problem_dir.to_str().unwrap()])
        .output()
        .expect("Failed to execute command");
    
    let stderr = String::from_utf8_lossy(&output.stderr);
    
    assert!(stderr.contains("Not a valid problem directory"));
    assert!(!output.status.success());
}