use std::path::PathBuf;
use cph::{Language, docker};

#[test]
fn test_docker_mount_paths() {
    // 各言語のマウントパスをテスト
    let languages = [Language::Rust, Language::PyPy];
    for lang in languages {
        let workspace_dir = PathBuf::from("test_workspace");
        let result = docker::run_in_docker(
            &workspace_dir,
            &lang,
            &["ls", "/compile"],
        );
        
        assert!(result.is_ok(), "Docker command failed for {:?}: {:?}", lang, result);
        let output = result.unwrap();
        assert!(output.status.success(), "Docker command returned non-zero status for {:?}", lang);
        
        // コンパイル環境のファイルが存在することを確認
        let stdout = String::from_utf8_lossy(&output.stdout);
        match lang {
            Language::Rust => {
                assert!(stdout.contains("Cargo.toml"), "Rust compile environment should contain Cargo.toml");
                assert!(stdout.contains("src"), "Rust compile environment should contain src directory");
            },
            Language::PyPy => {
                assert!(stdout.contains("main.py"), "PyPy compile environment should contain main.py");
            },
        }
    }
}

#[test]
fn test_docker_compile_rust() {
    let workspace_dir = PathBuf::from("test_workspace");
    let result = docker::run_in_docker(
        &workspace_dir,
        &Language::Rust,
        &["rustc", "--version"],
    );
    
    assert!(result.is_ok(), "Rust compiler check failed: {:?}", result);
    let output = result.unwrap();
    assert!(output.status.success(), "Rust compiler check returned non-zero status");
    
    let stdout = String::from_utf8_lossy(&output.stdout);
    assert!(stdout.contains("rustc"), "Rust compiler version should be displayed");
}

#[test]
fn test_docker_compile_pypy() {
    let workspace_dir = PathBuf::from("test_workspace");
    let result = docker::run_in_docker(
        &workspace_dir,
        &Language::PyPy,
        &["python3", "--version"],
    );
    
    assert!(result.is_ok(), "PyPy interpreter check failed: {:?}", result);
    let output = result.unwrap();
    assert!(output.status.success(), "PyPy interpreter check returned non-zero status");
    
    let stdout = String::from_utf8_lossy(&output.stdout);
    assert!(stdout.contains("Python"), "Python version should be displayed");
} 