mod io_test;
mod runners;

pub(crate) fn get_test_config_path() -> std::path::PathBuf {
    std::path::PathBuf::from("src/config/runner.yaml")
} 