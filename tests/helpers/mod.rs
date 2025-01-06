use std::fs;
use cph::config::Config;
use tempfile::TempDir;
use std::env;
use std::path::Path;
use std::process::Command;

thread_local! {
    static TEST_DIR: std::cell::RefCell<Option<TempDir>> = std::cell::RefCell::new(None);
}

pub mod docker_debug {
    use std::path::Path;
    use std::process::Command;

    pub fn inspect_directory(path: &Path) -> String {
        let output = Command::new("ls")
            .arg("-la")
            .arg(path)
            .output()
            .unwrap_or_else(|e| panic!("Failed to inspect directory: {}", e));

        String::from_utf8_lossy(&output.stdout).to_string()
    }

    pub fn inspect_docker_container(container_name: &str, path: &str) -> String {
        let output = Command::new("docker")
            .arg("exec")
            .arg(container_name)
            .arg("ls")
            .arg("-la")
            .arg(path)
            .output()
            .unwrap_or_else(|e| panic!("Failed to inspect container: {}", e));

        String::from_utf8_lossy(&output.stdout).to_string()
    }

    pub fn get_docker_logs(container_name: &str) -> String {
        let output = Command::new("docker")
            .arg("logs")
            .arg(container_name)
            .output()
            .unwrap_or_else(|e| panic!("Failed to get container logs: {}", e));

        String::from_utf8_lossy(&output.stdout).to_string()
    }
}

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