use cph::config::Config;

#[test]
fn test_config_load() {
    let config = Config::load().unwrap();
    
    // 言語設定の確認
    let default_lang = config.get::<String>("languages.default").unwrap();
    assert!(!default_lang.is_empty(), "デフォルト言語が設定されていません");

    // システム全体のDocker設定を確認
    let memory_limit = config.get::<u64>("system.docker.memory_limit_mb").unwrap();
    assert!(memory_limit > 0, "メモリ制限値が無効です");

    let mount_point = config.get::<String>("system.docker.mount_point").unwrap();
    assert!(!mount_point.is_empty(), "マウントポイントが設定されていません");
}

#[test]
fn test_language_config() {
    let config = Config::load().unwrap();
    
    // Rust言語の設定を確認
    let rust_image = config.get::<String>("languages.rust.runner.image").unwrap();
    assert!(!rust_image.is_empty(), "Rustのイメージが設定されていません");

    let rust_compile = config.get::<Vec<String>>("languages.rust.runner.compile").unwrap();
    assert!(!rust_compile.is_empty(), "Rustのコンパイルコマンドが設定されていません");

    // Python言語の設定を確認
    let python_image = config.get::<String>("languages.python.runner.image").unwrap();
    assert!(!python_image.is_empty(), "Pythonのイメージが設定されていません");

    let python_run = config.get::<Vec<String>>("languages.python.runner.run").unwrap();
    assert!(!python_run.is_empty(), "Pythonの実行コマンドが設定されていません");
} 