use std::fs;
use cph::config::Config;
use tempfile::TempDir;
use std::env;
use std::path::Path;
use std::process::Command;

thread_local! {
    static TEST_DIR: std::cell::RefCell<Option<TempDir>> = std::cell::RefCell::new(None);
}

pub mod docker_debug;

pub fn setup() {
    // テスト用の一時ディレクトリを作成
    let temp_dir = TempDir::new().unwrap();
    let temp_path = temp_dir.path().to_path_buf();

    // テスト用のディレクトリを作成
    fs::create_dir_all(temp_path.join("test-rust")).unwrap();
    fs::create_dir_all(temp_path.join("test-pypy")).unwrap();
    fs::create_dir_all(temp_path.join("test-cpp")).unwrap();

    // テスト用の環境変数を設定
    env::set_var("CPH_TEST_DIR", temp_path.join("test").to_str().unwrap());
    env::set_var("CPH_ACTIVE_DIR", temp_path.to_str().unwrap());

    // テスト用の設定を読み込む
    let _config = Config::load().unwrap();

    // 一時ディレクトリを保存
    TEST_DIR.with(|test_dir| {
        *test_dir.borrow_mut() = Some(temp_dir);
    });
}

pub fn teardown() {
    // 一時ディレクトリは自動的に削除されるため、
    // 明示的な削除処理は不要です
    TEST_DIR.with(|test_dir| {
        test_dir.borrow_mut().take();
    });
} 