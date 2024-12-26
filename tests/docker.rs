use std::path::PathBuf;
use std::fs;
use cph::{Language, docker};
use std::process::Output;

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

fn run_in_docker_and_check(workspace_dir: &PathBuf, lang: &Language, cmd: &[&str], error_msg: &str) -> Output {
    let result = docker::run_in_docker(workspace_dir, lang, cmd);
    assert!(result.is_ok(), "{}: {:?}", error_msg, result);
    let output = result.unwrap();
    assert!(output.status.success(), "{}", error_msg);
    output
}

fn test_hello_world(workspace_dir: &PathBuf, lang: Language, setup_cmd: &[&str], run_cmd: &[&str], expected_output: &str) {
    // ソースファイルの作成
    run_in_docker_and_check(
        workspace_dir,
        &lang,
        setup_cmd,
        &format!("Failed to create {:?} test file", lang),
    );

    // 実行
    let output = run_in_docker_and_check(
        workspace_dir,
        &lang,
        run_cmd,
        &format!("{:?} execution failed", lang),
    );
    
    assert_eq!(
        String::from_utf8_lossy(&output.stdout).trim(),
        expected_output,
        "Unexpected output from {:?} program",
        lang,
    );
}

#[test]
fn test_docker_mount_paths() {
    let workspace_dir = setup();
    // 各言語のマウントパスをテスト
    let languages = [Language::Rust, Language::PyPy];
    for lang in languages {
        let output = run_in_docker_and_check(
            &workspace_dir,
            &lang,
            &["ls", "/compile"],
            &format!("Docker command failed for {:?}", lang),
        );
        
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
    test_hello_world(
        &workspace_dir,
        Language::Rust,
        &["sh", "-c", r#"echo '
fn main() {
    println!("Hello from Rust!");
}' > test.rs"#],
        &["sh", "-c", "rustc test.rs -o /compile/test && cd /compile && ./test"],
        "Hello from Rust!",
    );
}

#[test]
fn test_docker_compile_pypy() {
    let workspace_dir = setup();
    test_hello_world(
        &workspace_dir,
        Language::PyPy,
        &["sh", "-c", r#"echo 'print("Hello from PyPy!")' > /compile/test.py"#],
        &["sh", "-c", "cd /compile && pypy3 test.py"],
        "Hello from PyPy!",
    );
} 