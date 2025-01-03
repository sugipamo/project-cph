use std::fs;
use cph::config::Config;

pub fn setup() {
    // テスト用の設定を読み込む
    let config = Config::load().unwrap();
    
    // マウントポイントディレクトリを作成
    let mount_point = config.get::<String>("system.docker.mount_point").unwrap();
    fs::create_dir_all(&mount_point).unwrap();
}

pub fn teardown() {
    // テスト用の設定を読み込む
    let config = Config::load().unwrap();
    
    // マウントポイントディレクトリを削除
    let mount_point = config.get::<String>("system.docker.mount_point").unwrap();
    let _ = fs::remove_dir_all(&mount_point);
} 