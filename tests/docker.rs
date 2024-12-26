use std::path::PathBuf;
use std::fs;
use cph::{Language, docker};

fn setup() {
    // テストディレクトリの準備
    let workspace = PathBuf::from("test_workspace");
    if workspace.exists() {
        fs::remove_dir_all(&workspace).unwrap();
    }
    fs::create_dir_all(&workspace).unwrap();
}

#[test]
fn test_docker_mount_paths() {
    setup();
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
    setup();
    let workspace_dir = PathBuf::from("test_workspace");
    
    // テスト用のRustファイルを作成
    fs::write(
        workspace_dir.join("test.rs"),
        r#"
fn main() {
    println!("Hello from Rust!");
}
"#,
    ).unwrap();

    // コンパイル
    let result = docker::run_in_docker(
        &workspace_dir,
        &Language::Rust,
        &["rustc", "test.rs"],
    );
    assert!(result.is_ok(), "Rust compilation failed: {:?}", result);
    assert!(result.unwrap().status.success(), "Rust compilation returned non-zero status");

    // 実行
    let result = docker::run_in_docker(
        &workspace_dir,
        &Language::Rust,
        &["./test"],
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
    setup();
    let workspace_dir = PathBuf::from("test_workspace");
    
    // テスト用のPythonファイルを作成
    fs::write(
        workspace_dir.join("test.py"),
        r#"
print("Hello from PyPy!")
"#,
    ).unwrap();

    // 実行
    let result = docker::run_in_docker(
        &workspace_dir,
        &Language::PyPy,
        &["python3", "test.py"],
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