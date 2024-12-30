use std::path::PathBuf;
use tempfile::TempDir;
use tokio;

/// テスト環境をセットアップする
pub async fn setup_test_environment() -> PathBuf {
    // 一時ディレクトリを作成
    let temp_dir = TempDir::new()
        .expect("一時ディレクトリの作成に失敗しました")
        .into_path();

    // テスト用のディレクトリ構造を作成
    let test_dirs = [
        "active_contest",
        "active_contest/template",
        "active_contest/test",
        "contests",
        "src/config",
    ];

    for dir in test_dirs.iter() {
        tokio::fs::create_dir_all(temp_dir.join(dir))
            .await
            .expect("テストディレクトリの作成に失敗しました");
    }

    // テスト用の設定ファイルをコピー
    setup_test_config(&temp_dir).await;

    temp_dir
}

/// テスト用の設定ファイルを作成
async fn setup_test_config(test_dir: &PathBuf) {
    // languages.yaml
    let languages_yaml = r#"
languages:
  rust:
    display_name: "Rust (1.42.0)"
    extension: "rs"
    site_ids:
      atcoder: "4050"
    runner:
      image: "rust:1.42.0"
      compile: "rustc {source} -o {binary}"
      run: "./{binary}"
      compile_dir: "/workspace"
  python:
    display_name: "Python (3.8.2)"
    extension: "py"
    site_ids:
      atcoder: "4006"
    runner:
      image: "python:3.8.2"
      run: "python {source}"
      compile_dir: "/workspace"
"#;

    // docker.yaml
    let docker_yaml = r#"
timeout_seconds: 5
memory_limit_mb: 512
mount_point: "/workspace"
"#;

    // sites.yaml
    let sites_yaml = r#"
sites:
  atcoder:
    aliases:
      - at-coder
      - at_coder
      - AtCoder
      - ac
    url_pattern: "https://atcoder.jp/contests/{contest_id}/tasks/{problem_id}"
"#;

    // 設定ファイルを書き込む
    let config_files = [
        ("languages.yaml", languages_yaml),
        ("docker.yaml", docker_yaml),
        ("sites.yaml", sites_yaml),
    ];

    for (filename, content) in config_files.iter() {
        tokio::fs::write(
            test_dir.join("src/config").join(filename),
            content.trim(),
        )
        .await
        .expect(&format!("{}の作成に失敗しました", filename));
    }
}

/// テスト用のテンプレートファイルを作成
pub async fn setup_test_templates(test_dir: &PathBuf) {
    let templates = [
        ("rust", "main.rs", r#"
use proconio::input;

fn main() {
    input! {
        n: i32,
    }
    println!("{}", n);
}
"#),
        ("python", "main.py", r#"
def solve():
    n = int(input())
    print(n)

if __name__ == '__main__':
    solve()
"#),
    ];

    for (lang, filename, content) in templates.iter() {
        let template_dir = test_dir
            .join("active_contest/template")
            .join(lang);
        
        tokio::fs::create_dir_all(&template_dir)
            .await
            .expect("テンプレートディレクトリの作成に失敗しました");

        tokio::fs::write(
            template_dir.join(filename),
            content.trim(),
        )
        .await
        .expect("テンプレートファイルの作成に失敗しました");
    }
}

/// コマンドの実行結果を検証する
pub fn verify_command_result<T>(result: Result<T, Box<dyn std::error::Error>>) {
    match result {
        Ok(_) => (),
        Err(e) => panic!("コマンドの実行に失敗しました: {}", e),
    }
}

/// ディレクトリ構造を検証する
pub async fn verify_directory_structure(test_dir: &PathBuf, contest_id: &str) {
    let required_paths = [
        format!("active_contest"),
        format!("active_contest/template"),
        format!("active_contest/test"),
        format!("contests"),
        format!("contests/{}", contest_id),
    ];

    for path in required_paths.iter() {
        let full_path = test_dir.join(path);
        assert!(
            full_path.exists(),
            "必要なディレクトリが存在しません: {}",
            full_path.display()
        );
    }
}

/// ファイルの内容を検証する
pub async fn verify_file_contents(file_path: &PathBuf, expected_content: &str) {
    let content = tokio::fs::read_to_string(file_path)
        .await
        .expect("ファイルの読み込みに失敗しました");
    
    assert_eq!(
        content.trim(),
        expected_content.trim(),
        "ファイルの内容が期待と異なります: {}",
        file_path.display()
    );
} 