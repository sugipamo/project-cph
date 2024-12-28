mod config_test;
mod runner_test;
mod container_test;
mod io_test;

use std::path::PathBuf;
use tokio;

// テストで使用する設定ファイルのパスを取得
fn get_test_config_path() -> PathBuf {
    PathBuf::from(env!("CARGO_MANIFEST_DIR"))
        .join("tests")
        .join("fixtures")
        .join("docker")
        .join("runner.yaml")
} 