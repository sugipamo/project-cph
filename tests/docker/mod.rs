#[cfg(test)]
mod runner_test;
#[cfg(test)]
mod config_test;

use std::process::Command;

// Dockerデーモンが利用可能かチェックする
pub fn check_docker_available() -> bool {
    Command::new("docker")
        .arg("info")
        .output()
        .map(|output| output.status.success())
        .unwrap_or(false)
}

// テストの前に実行される初期化処理
pub fn setup() {
    if !check_docker_available() {
        panic!("Dockerデーモンが利用できません。Dockerが起動していることを確認してください。");
    }
}

// テストの後に実行されるクリーンアップ処理
pub fn teardown() {
    // 必要に応じてコンテナやイメージのクリーンアップを実行
} 