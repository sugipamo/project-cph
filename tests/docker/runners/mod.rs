use bollard::Docker;
use std::time::Duration;
use cph::docker::{DockerRunners, RunnerConfig, RunnerState};
use std::path::PathBuf;
use crate::helpers::{load_test_languages, setup_test_templates, cleanup_test_files};

#[tokio::test]
async fn test_basic_pipeline() {
    setup_test_templates();
    let _lang_config = load_test_languages();
    let test_lang = "python".to_string();

    // 設定の読み込み
    let config_path = PathBuf::from("src/config/docker.yaml");
    let config = RunnerConfig::load(&config_path).unwrap();
    let docker = Docker::connect_with_local_defaults().unwrap();
    let runners = DockerRunners::new(docker, config);

    // 2つのRunnerを作成（generator -> solver）
    let gen_id = runners.add_runner(test_lang.clone()).await.unwrap();
    let sol_id = runners.add_runner(test_lang.clone()).await.unwrap();
    runners.connect(gen_id, sol_id).await.unwrap();

    // ジェネレータ: 1から10までの数を出力
    runners.run_code(gen_id, r#"
for i in range(1, 11):
    print(i)
"#).await.unwrap();

    // ソルバー: 入力を2倍して出力
    runners.run_code(sol_id, r#"
while True:
    try:
        n = int(input())
        print(n * 2)
    except EOFError:
        break
"#).await.unwrap();

    // 実行
    runners.run().await.unwrap();

    // 実行時間を確認
    let execution_time = runners.get_execution_time().await.unwrap();
    assert!(execution_time < Duration::from_secs(5));

    // 最終状態を確認
    assert_eq!(runners.get_state().await, RunnerState::Stop);
    cleanup_test_files();
}

#[tokio::test]
async fn test_error_handling() {
    setup_test_templates();
    let _lang_config = load_test_languages();
    let test_lang = "python".to_string();

    let config_path = PathBuf::from("src/config/docker.yaml");
    let config = RunnerConfig::load(&config_path).unwrap();
    let docker = Docker::connect_with_local_defaults().unwrap();
    let runners = DockerRunners::new(docker, config);

    // エラーを発生させるRunnerを作成
    let id = runners.add_runner(test_lang.clone()).await.unwrap();

    // 無効なPythonコード
    runners.run_code(id, "invalid python code").await.unwrap();

    // 実行
    let result = runners.run().await;
    assert!(result.is_err());
    assert_eq!(runners.get_state().await, RunnerState::Error);
    cleanup_test_files();
}

#[tokio::test]
async fn test_multi_stage_pipeline() {
    setup_test_templates();
    let _lang_config = load_test_languages();
    let test_lang = "python".to_string();

    let config_path = PathBuf::from("src/config/docker.yaml");
    let config = RunnerConfig::load(&config_path).unwrap();
    let docker = Docker::connect_with_local_defaults().unwrap();
    let runners = DockerRunners::new(docker, config);

    // 3段階のパイプライン（generator -> validator -> solver）
    let gen_id = runners.add_runner(test_lang.clone()).await.unwrap();
    let val_id = runners.add_runner(test_lang.clone()).await.unwrap();
    let sol_id = runners.add_runner(test_lang.clone()).await.unwrap();

    // 接続を設定
    runners.connect(gen_id, val_id).await.unwrap();
    runners.connect(val_id, sol_id).await.unwrap();

    // ジェネレータ: 1から5までの数を出力
    runners.run_code(gen_id, r#"
for i in range(1, 6):
    print(i)
"#).await.unwrap();

    // バリデータ: 偶数のみを通過
    runners.run_code(val_id, r#"
while True:
    try:
        n = int(input())
        if n % 2 == 0:
            print(n)
    except EOFError:
        break
"#).await.unwrap();

    // ソルバー: 入力を2倍
    runners.run_code(sol_id, r#"
while True:
    try:
        n = int(input())
        print(n * 2)
    except EOFError:
        break
"#).await.unwrap();

    // 実行
    runners.run().await.unwrap();
    assert_eq!(runners.get_state().await, RunnerState::Stop);
    cleanup_test_files();
}

#[tokio::test]
async fn test_timeout() {
    setup_test_templates();
    let _lang_config = load_test_languages();
    let test_lang = "python".to_string();

    let config_path = PathBuf::from("src/config/docker.yaml");
    let config = RunnerConfig::load(&config_path).unwrap();
    let docker = Docker::connect_with_local_defaults().unwrap();
    let runners = DockerRunners::new(docker, config);

    // 無限ループを実行するRunner
    let id = runners.add_runner(test_lang.clone()).await.unwrap();
    runners.run_code(id, "while True: pass").await.unwrap();

    // 実行（タイムアウトするはず）
    let result = runners.run().await;
    assert!(result.is_err());
    assert_eq!(runners.get_state().await, RunnerState::Error);
    cleanup_test_files();
}

#[tokio::test]
async fn test_large_output() {
    setup_test_templates();
    let _lang_config = load_test_languages();
    let test_lang = "python".to_string();

    let config_path = PathBuf::from("src/config/docker.yaml");
    let config = RunnerConfig::load(&config_path).unwrap();
    let docker = Docker::connect_with_local_defaults().unwrap();
    let runners = DockerRunners::new(docker, config);

    // 大きな出力を生成するRunner
    let id1 = runners.add_runner(test_lang.clone()).await.unwrap();
    let id2 = runners.add_runner(test_lang.clone()).await.unwrap();
    runners.connect(id1, id2).await.unwrap();

    // 2MB以上の出力を生成
    runners.run_code(id1, r#"print('a' * (2 * 1024 * 1024))"#).await.unwrap();
    runners.run_code(id2, "print(input())").await.unwrap();

    // 実行（バッファサイズエラーになるはず）
    let result = runners.run().await;
    assert!(result.is_err());
    cleanup_test_files();
} 