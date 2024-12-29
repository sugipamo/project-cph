mod io_test;
mod runners;
mod config_test;

pub(crate) fn get_test_config_path() -> std::path::PathBuf {
    std::path::PathBuf::from("src/config/runner.yaml")
} 