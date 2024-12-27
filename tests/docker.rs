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
    let result = docker::run_in_docker(workspace_dir, lang, cmd, None).await;
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
async fn test_docker_compile_pypy() {
    let workspace_dir = setup();
    test_hello_world(
        &workspace_dir,
        Language::PyPy,
        &["sh", "-c", r#"echo 'print("Hello from PyPy!")' > /compile/main.py"#],
        &["pypy3", "/compile/main.py"],
        "Hello from PyPy!",
    ).await;
} 