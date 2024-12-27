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
    
    // compile/pypyディレクトリを作成
    fs::create_dir_all(workspace.path().join("compile/pypy")).unwrap();
    // パーミッションを設定
    #[cfg(unix)]
    {
        use std::os::unix::fs::PermissionsExt;
        fs::set_permissions(
            workspace.path().join("compile/pypy"),
            fs::Permissions::from_mode(0o777),
        ).unwrap();
    }
    
    // compile/rustディレクトリを作成
    fs::create_dir_all(workspace.path().join("compile/rust/src")).unwrap();
    // パーミッションを設定
    #[cfg(unix)]
    {
        use std::os::unix::fs::PermissionsExt;
        fs::set_permissions(
            workspace.path().join("compile/rust"),
            fs::Permissions::from_mode(0o777),
        ).unwrap();
        fs::set_permissions(
            workspace.path().join("compile/rust/src"),
            fs::Permissions::from_mode(0o777),
        ).unwrap();
    }
    
    // Cargo.tomlを作成
    fs::write(
        workspace.path().join("compile/rust/Cargo.toml"),
        r#"[package]
name = "compile"
version = "0.1.0"
edition = "2021"

[[bin]]
name = "a"
path = "src/a.rs"
"#
    ).unwrap();
    
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

#[test]
fn test_test_command_requires_workspace() {
    let workspace = setup_workspace();
    
    // ワークスペースを設定せずにテストを実行しようとする
    run_command(&["atcoder", "test", "a"], Some(&workspace))
        .failure()
        .stderr(contains("No active contest"));
}

#[test]
fn test_test_command_file_not_exists() {
    let workspace = setup_workspace_with_contest("abc001");
    
    // 存在しないファイルのテストを実行
    run_command(&["atcoder", "test", "a"], Some(&workspace))
        .failure()
        .stderr(contains("Problem file"));
}

#[test]
fn test_test_command_pypy() {
    let workspace = setup_workspace_with_contest("abc001");
    
    // PyPyを選択
    run_command(&["atcoder", "language", "py-py"], Some(&workspace))
        .success();
    
    // テストファイルを作成
    fs::create_dir_all(workspace.path().join("workspace/test/a")).unwrap();
    fs::write(
        workspace.path().join("workspace/test/a/sample-1.in"),
        "1\n"
    ).unwrap();
    fs::write(
        workspace.path().join("workspace/test/a/sample-1.out"),
        "1\n"
    ).unwrap();
    
    // PyPyのソースファイルを作成
    fs::write(
        workspace.path().join("workspace/a.py"),
        "n = int(input())\nprint(n)\n"
    ).unwrap();
    
    // main.pyを作成
    let main_py_path = workspace.path().join("compile/pypy/main.py");
    fs::write(&main_py_path, "n = int(input())\nprint(n)\n").unwrap();
    
    // パーミッションを設定
    #[cfg(unix)]
    {
        use std::os::unix::fs::PermissionsExt;
        fs::set_permissions(&main_py_path, fs::Permissions::from_mode(0o777)).unwrap();
    }
    
    // テストを実行
    run_command(&["atcoder", "test", "a"], Some(&workspace))
        .success()
        .stdout(contains("Test case sample-1 ... passed"));
}

#[test]
fn test_test_command_rust() {
    let workspace = setup_workspace_with_contest("abc001");
    
    // テストファイルを作成
    fs::create_dir_all(workspace.path().join("workspace/test/a")).unwrap();
    fs::write(
        workspace.path().join("workspace/test/a/sample-1.in"),
        "1\n"
    ).unwrap();
    fs::write(
        workspace.path().join("workspace/test/a/sample-1.out"),
        "1\n"
    ).unwrap();
    
    // Rustのソースファイルを作成
    fs::write(
        workspace.path().join("workspace/a.rs"),
        r#"fn main() {
    let mut line = String::new();
    std::io::stdin().read_line(&mut line).unwrap();
    let n: i32 = line.trim().parse().unwrap();
    println!("{}", n);
}"#
    ).unwrap();
    
    // ソースファイルをコンパイルディレクトリにコピー
    let rust_src_path = workspace.path().join("compile/rust/src/a.rs");
    fs::write(
        &rust_src_path,
        r#"fn main() {
    let mut line = String::new();
    std::io::stdin().read_line(&mut line).unwrap();
    let n: i32 = line.trim().parse().unwrap();
    println!("{}", n);
}"#
    ).unwrap();
    
    // テーミッションを設定
    #[cfg(unix)]
    {
        use std::os::unix::fs::PermissionsExt;
        fs::set_permissions(&rust_src_path, fs::Permissions::from_mode(0o777)).unwrap();
        fs::set_permissions(
            workspace.path().join("compile/rust/Cargo.toml"),
            fs::Permissions::from_mode(0o777)
        ).unwrap();
    }
    
    // テストを実行
    run_command(&["atcoder", "test", "a"], Some(&workspace))
        .success()
        .stdout(contains("Test case sample-1 ... passed"));
} 