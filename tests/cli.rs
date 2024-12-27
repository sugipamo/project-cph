use assert_cmd::Command;
use predicates::str::contains;
use std::fs;
use tempfile::TempDir;

fn run_command(args: &[&str], workspace: Option<&TempDir>) -> assert_cmd::assert::Assert {
    let mut command = Command::cargo_bin("cph").unwrap();
    command.env("TEST_MODE", "1");
    command.args(args);
    if let Some(dir) = workspace {
        command.current_dir(dir.path());
    }
    command.assert()
}

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

    // .moveignoreを作成
    fs::write(
        temp.path().join("src/templates/.moveignore"),
        ".archiveignore\n\n# テンプレートファイル - コンテスト間で共有\ntemplate/\ntemplate/**\n"
    ).unwrap();

    temp
}

fn setup_workspace_with_contest(contest_id: &str) -> TempDir {
    let workspace = setup_workspace();
    run_command(&["atcoder", "workspace", contest_id], Some(&workspace))
        .success();
    workspace
}

#[test]
fn test_invalid_site() {
    run_command(&["invalid", "login"], None)
        .failure()
        .stderr(contains("unrecognized subcommand 'invalid'"));
}

#[test]
fn test_invalid_command() {
    run_command(&["atcoder", "invalid"], None)
        .failure()
        .stderr(contains("unrecognized subcommand 'invalid'"));
}

#[test]
fn test_login_command() {
    run_command(&["atcoder", "login"], None)
        .success();
}

#[test]
fn test_workspace_command() {
    let workspace = setup_workspace();
    
    // ワークスペースを設定
    run_command(&["atcoder", "workspace", "abc001"], Some(&workspace))
        .success();

    // ディレクトリ構造を確認
    assert!(workspace.path().join("workspace").exists());
    assert!(workspace.path().join("workspace/contests.yaml").exists());
    assert!(workspace.path().join("workspace/.moveignore").exists());

    // contests.yamlの内容を確認
    let config = fs::read_to_string(workspace.path().join("workspace/contests.yaml")).unwrap();
    assert!(config.contains("contest: abc001"));
    assert!(config.contains("language: rust")); // デフォルト言語
    assert!(config.contains("site: atcoder"));
}

#[test]
fn test_language_command() {
    let workspace = setup_workspace_with_contest("abc001");
    run_command(&["atcoder", "language", "py-py"], Some(&workspace))
        .success();
}

#[test]
fn test_language_command_requires_workspace() {
    let workspace = setup_workspace();
    
    // ワークスペースを設定せずに言語を設定しようとする
    run_command(&["atcoder", "language", "rust"], Some(&workspace))
        .failure()
        .stderr(contains("No active contest"));
}

#[test]
fn test_open_command() {
    let workspace = setup_workspace_with_contest("abc001");
    run_command(&["atcoder", "open", "a"], Some(&workspace))
        .success();
    assert!(workspace.path().join("workspace/a.rs").exists());
}

#[test]
fn test_open_command_requires_workspace() {
    let workspace = setup_workspace();
    
    // ワークスペースを設定せずに問題を開こうとする
    run_command(&["atcoder", "open", "a"], Some(&workspace))
        .failure()
        .stderr(contains("No active contest"));
}

#[test]
fn test_workspace_switch() {
    let workspace = setup_workspace();
    
    // 最初のワークスペースを設定
    run_command(&["atcoder", "workspace", "abc001"], Some(&workspace))
        .success();

    // 問題を開く
    run_command(&["atcoder", "open", "a"], Some(&workspace))
        .success();

    // 別のワークスペースに切り替え
    run_command(&["atcoder", "workspace", "abc002"], Some(&workspace))
        .success();

    // 元のワークスペースがアーカイブされていることを確認
    assert!(workspace.path().join("contests/abc001").exists());
    assert!(workspace.path().join("contests/abc001/a.rs").exists());

    // 新しいワークスペースが作成されていることを確認
    assert!(workspace.path().join("workspace").exists());
    assert!(workspace.path().join("workspace/contests.yaml").exists());
    assert!(workspace.path().join("workspace/.moveignore").exists());
} 