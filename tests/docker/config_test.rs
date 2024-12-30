use crate::helpers::load_test_languages;
use cph::docker::config::RunnerConfig;
use std::path::PathBuf;

#[test]
fn test_load_runner_config() {
    super::setup();

    let config = RunnerConfig::load(PathBuf::from("src/config/docker.yaml")).unwrap();
    
    // 基本設定の検証
    assert_eq!(config.timeout_seconds, 5);
    assert_eq!(config.memory_limit_mb, 512);
    assert_eq!(config.mount_point, "/workspace");

    super::teardown();
}

#[test]
fn test_language_config() {
    super::setup();

    let config = RunnerConfig::load(PathBuf::from("src/config/docker.yaml")).unwrap();
    let lang_config = load_test_languages();

    // 各言語の設定をテスト
    for (lang_name, lang_info) in &lang_config.languages {
        let runner_config = config.get_language_config(lang_name).unwrap();
        assert_eq!(runner_config.image, lang_info.runner.image);
        assert_eq!(runner_config.compile, lang_info.runner.compile);
        assert_eq!(runner_config.run, lang_info.runner.run);
        assert_eq!(runner_config.compile_dir, lang_info.runner.compile_dir);
    }

    // 無効な言語の検証
    assert!(config.get_language_config("invalid").is_none());

    super::teardown();
} 