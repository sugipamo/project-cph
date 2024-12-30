use std::path::PathBuf;
use tempfile::TempDir;
use tokio;
use crate::helpers::{load_test_languages, setup_test_templates as setup_common_templates};
use std::fs;

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

    // 共通のテンプレートをセットアップ
    setup_common_templates();

    temp_dir
}

/// テスト用の設定ファイルを作成
async fn setup_test_config(test_dir: &PathBuf) {
    // 既存の設定ファイルをコピー
    let config_files = [
        ("languages.yaml", "src/config/languages.yaml"),
        ("docker.yaml", "src/config/docker.yaml"),
        ("sites.yaml", "src/config/sites.yaml"),
    ];

    for (filename, source_path) in config_files.iter() {
        let content = fs::read_to_string(source_path)
            .unwrap_or_else(|_| panic!("{}の読み込みに失敗しました", source_path));

        tokio::fs::write(
            test_dir.join("src/config").join(filename),
            content.trim(),
        )
        .await
        .expect(&format!("{}の作成に失敗しました", filename));
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