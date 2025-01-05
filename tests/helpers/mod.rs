use std::fs;
use cph::config::Config;

pub fn setup() {
    // テスト用の設定を読み込む
    let _config = Config::load().unwrap();
    
    // マスト用のディレクトリを作成
    fs::create_dir_all("/tmp/test-rust").unwrap();
    fs::create_dir_all("/tmp/test-pypy").unwrap();
    fs::create_dir_all("/tmp/test-cpp").unwrap();
}

pub fn teardown() {
    // テスト用のディレクトリを削除
    let _ = fs::remove_dir_all("/tmp/test-rust");
    let _ = fs::remove_dir_all("/tmp/test-pypy");
    let _ = fs::remove_dir_all("/tmp/test-cpp");
} 