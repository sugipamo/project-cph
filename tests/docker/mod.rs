use std::process::Command;

mod config_test;
mod runners;
mod io_test;

/// Dockerデーモンが利用可能かチェックする
fn check_docker_available() -> bool {
    Command::new("docker")
        .arg("info")
        .output()
        .map(|output| output.status.success())
        .unwrap_or(false)
}

/// テストの前に実行される初期化処理
#[cfg(test)]
pub fn setup() {
    if !check_docker_available() {
        panic!("Dockerデーモンが利用できません。Dockerが起動していることを確認してください。");
    }
}

/// テストの後に実行されるクリーンアップ処理
#[cfg(test)]
pub fn teardown() {
    // 必要に応じてコンテナやイメージのクリーンアップを実行
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_docker_available() {
        assert!(check_docker_available(), "Dockerが利用できません");
    }
} 