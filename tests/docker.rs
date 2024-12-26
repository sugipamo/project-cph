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

async fn run_in_docker_and_check(workspace_dir: &PathBuf, lang: &Language, cmd: &[&str], error_msg: &str) -> (String, String) {
    let result = docker::run_in_docker(workspace_dir, lang, cmd).await;
    assert!(result.is_ok(), "{}: {:?}", error_msg, result);
    result.unwrap()
}

async fn test_hello_world(workspace_dir: &PathBuf, lang: Language, setup_cmd: &[&str], run_cmd: &[&str], expected_output: &str) {
    // ソースファイルの作成
    let (_, _) = run_in_docker_and_check(
        workspace_dir,
        &lang,
        setup_cmd,
        &format!("Failed to create {:?} test file", lang),
    ).await;

    // 実行
    let (stdout, _) = run_in_docker_and_check(
        workspace_dir,
        &lang,
        run_cmd,
        &format!("{:?} execution failed", lang),
    ).await;
    
    assert_eq!(
        stdout.trim(),
        expected_output,
        "Unexpected output from {:?} program",
        lang,
    );
}

#[tokio::test]
async fn test_docker_mount_paths() {
    let workspace_dir = setup();
    // 各言語のマウントパスをテスト
    let languages = [Language::Rust, Language::PyPy];
    for lang in languages {
        let (stdout, _) = run_in_docker_and_check(
            &workspace_dir,
            &lang,
            &["ls", "/compile"],
            &format!("Docker command failed for {:?}", lang),
        ).await;
        
        // コンパイル環境のファイルが存在することを確認
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

#[tokio::test]
async fn test_docker_compile_rust() {
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
    ).await;
}

#[tokio::test]
async fn test_docker_compile_pypy() {
    let workspace_dir = setup();
    test_hello_world(
        &workspace_dir,
        Language::PyPy,
        &["sh", "-c", r#"echo 'print("Hello from PyPy!")' > /compile/test.py"#],
        &["sh", "-c", "cd /compile && pypy3 test.py"],
        "Hello from PyPy!",
    ).await;
}

#[tokio::test]
async fn test_oj_tool() {
    let workspace_dir = setup();
    
    // バージョン確認
    let result = docker::run_oj_tool(&workspace_dir, &["--version"]).await;
    assert!(result.is_ok(), "Failed to run oj tool: {:?}", result);
    let (stdout, _) = result.unwrap();
    assert!(stdout.contains("online-judge-tools"), "Unexpected version output: {}", stdout);
    assert!(stdout.contains("online-judge-api-client"), "Missing API client version: {}", stdout);

    // テストケースのダウンロードテスト（AOJのサンプル問題を使用）
    let result = docker::run_oj_tool(
        &workspace_dir,
        &["download", "https://judge.u-aizu.ac.jp/onlinejudge/description.jsp?id=ITP1_1_A"]
    ).await;
    assert!(result.is_ok(), "Failed to download test cases: {:?}", result);

    // ダウンロードされたファイルの確認
    let (files, _) = run_in_docker_and_check(
        &workspace_dir,
        &Language::PyPy,  // どの言語でも良いので、PyPyを使用
        &["ls"],
        "Failed to list downloaded files",
    ).await;
    assert!(files.contains("test"), "Test directory not found");
} 