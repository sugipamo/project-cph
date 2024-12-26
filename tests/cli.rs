use assert_cmd::Command;
use predicates::str::contains;
use std::fs;
use tempfile::TempDir;

fn setup_workspace() -> TempDir {
    let temp = TempDir::new().unwrap();
    
    // テンプレートディレクトリを作成
    fs::create_dir_all(temp.path().join("src/templates/template")).unwrap();
    
    // Rustテンプレートを作成
    fs::write(
        temp.path().join("src/templates/template/main.rs"),
        "fn main() {\n    println!(\"Hello, World!\");\n}\n"
    ).unwrap();
    
    // PyPyテンプレートを作成
    fs::write(
        temp.path().join("src/templates/template/main.py"),
        "print('Hello, World!')\n"
    ).unwrap();
    
    temp
}

fn run_command(args: &[&str], workspace: Option<&TempDir>) -> assert_cmd::assert::Assert {
    let mut cmd = Command::cargo_bin("cph").unwrap();
    if let Some(dir) = workspace {
        cmd.current_dir(dir.path());
    }
    cmd.env("TEST_MODE", "1")
       .args(args)
       .assert()
}

#[test]
fn test_invalid_site() {
    run_command(&["invalid", "login"], None)
        .failure()
        .stderr(contains("invalid value 'invalid' for '<SITE>'"));
}

#[test]
fn test_invalid_command() {
    run_command(&["atcoder", "invalid"], None)
        .failure()
        .stderr(contains("invalid command: 'invalid'"));
}

#[test]
fn test_open_command_requires_args() {
    run_command(&["atcoder", "open"], None)
        .failure()
        .stderr(contains("the following required arguments were not provided:"));
}

#[test]
fn test_open_command() {
    let workspace = setup_workspace();
    
    // 新しい問題をセットアップ
    run_command(&["atcoder", "open", "abc001", "rust", "a"], Some(&workspace))
        .success();

    // ディレクトリ構造を確認
    assert!(workspace.path().join("workspace").exists());
    assert!(workspace.path().join("workspace/abc001").exists());
    assert!(workspace.path().join("workspace/abc001/a.rs").exists());
    assert!(workspace.path().join("contests.yaml").exists());

    // contests.yamlの内容を確認
    let config = fs::read_to_string(workspace.path().join("contests.yaml")).unwrap();
    assert!(config.contains("abc001"));
    assert!(config.contains("rust"));
    assert!(config.contains("atcoder"));

    // 別の問題をセットアップ（前の問題は自動的にアーカイブされる）
    run_command(&["atcoder", "open", "abc002", "rust", "b"], Some(&workspace))
        .success();

    // アーカイブされたことを確認
    assert!(workspace.path().join("contests/abc001").exists());
    assert!(workspace.path().join("contests/abc001/a.rs").exists());

    // 新しい問題のファイルが作成されていることを確認
    assert!(workspace.path().join("workspace/abc002").exists());
    assert!(workspace.path().join("workspace/abc002/b.rs").exists());
}

#[test]
fn test_login_command() {
    run_command(&["atcoder", "login"], None)
        .success();
} 