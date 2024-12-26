use std::path::PathBuf;
use std::fs;
use cph::{Language, docker};

fn get_test_workspace() -> PathBuf {
    std::env::current_dir()
        .unwrap_or_else(|_| PathBuf::from("."))
        .join("tests")
        .join("test_workspace")
}

fn setup() -> PathBuf {
    // テストディレクトリの準備
    let workspace = get_test_workspace();
    if workspace.exists() {
        let _ = fs::remove_dir_all(&workspace);
    }
    fs::create_dir_all(&workspace).expect("Failed to create test workspace");
    workspace
}

#[test]
fn test_docker_mount_paths() {
    let workspace_dir = setup();
    // 各言語のマウントパスをテスト
    let languages = [Language::Rust, Language::PyPy];
    for lang in languages {
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
    let workspace_dir = setup();
    
    // テスト用のRustファイルを作成
    fs::write(
        workspace_dir.join("test.rs"),
        r#"
fn main() {
    println!("Hello from Rust!");
}
"#,
    ).expect("Failed to write test file");

    // コンパイル（出力先を/compileに指定）
    let result = docker::run_in_docker(
        &workspace_dir,
        &Language::Rust,
        &["rustc", "test.rs", "-o", "/compile/test"],
    );
    assert!(result.is_ok(), "Rust compilation failed: {:?}", result);
    assert!(result.unwrap().status.success(), "Rust compilation returned non-zero status");

    // 実行（/compileディレクトリから実行）
    let result = docker::run_in_docker(
        &workspace_dir,
        &Language::Rust,
        &["sh", "-c", "cd /compile && ./test"],
    );
    assert!(result.is_ok(), "Rust execution failed: {:?}", result);
    let output = result.unwrap();
    assert!(output.status.success(), "Rust execution returned non-zero status");
    assert_eq!(
        String::from_utf8_lossy(&output.stdout).trim(),
        "Hello from Rust!",
        "Unexpected output from Rust program"
    );
}

#[test]
fn test_docker_compile_pypy() {
    let workspace_dir = setup();
    
    // テスト用のPythonファイルを作成（/compileディレクトリに直接作成）
    let result = docker::run_in_docker(
        &workspace_dir,
        &Language::PyPy,
        &["sh", "-c", r#"echo 'print("Hello from PyPy!")' > /compile/test.py"#],
    );
    assert!(result.is_ok(), "Failed to create PyPy test file: {:?}", result);
    assert!(result.unwrap().status.success(), "Failed to create PyPy test file");

    // 実行（/compileディレクトリから実行）
    let result = docker::run_in_docker(
        &workspace_dir,
        &Language::PyPy,
        &["sh", "-c", "cd /compile && pypy3 test.py"],
    );
    
    assert!(result.is_ok(), "PyPy execution failed: {:?}", result);
    let output = result.unwrap();
    assert!(output.status.success(), "PyPy execution returned non-zero status");
    assert_eq!(
        String::from_utf8_lossy(&output.stdout).trim(),
        "Hello from PyPy!",
        "Unexpected output from PyPy program"
    );
} 