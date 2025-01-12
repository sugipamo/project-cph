use std::path::PathBuf;
use anyhow::Result;
use project_cph::process::{
    ProcessExecutor,
    test::{TestCase, TestSuite, TestResult},
    test::runner::TestRunner,
};
use project_cph::config::Config;

#[tokio::test]
async fn test_basic_process_execution() -> Result<()> {
    // 設定を読み込み
    let config = Config::get_default_config()?;
    let executor = ProcessExecutor::new(config);
    let runner = TestRunner::new(executor);

    // 単純な加算プログラムのテスト
    let source = r#"
fn main() {
    let mut input = String::new();
    std::io::stdin().read_line(&mut input).unwrap();
    let nums: Vec<i32> = input
        .split_whitespace()
        .map(|x| x.parse().unwrap())
        .collect();
    println!("{}", nums[0] + nums[1]);
}
"#;

    // ソースファイルを作成
    let temp_dir = tempfile::tempdir()?;
    let source_path = temp_dir.path().join("main.rs");
    std::fs::write(&source_path, source)?;

    // コンパイル
    let output_path = temp_dir.path().join("main");
    std::process::Command::new("rustc")
        .arg(&source_path)
        .arg("-o")
        .arg(&output_path)
        .output()?;

    // テストケースを作成
    let test_cases = vec![
        TestCase::new("1 2\n".to_string(), "3\n".to_string()),
        TestCase::new("10 20\n".to_string(), "30\n".to_string()),
        TestCase::with_limits(
            "100 200\n".to_string(),
            "300\n".to_string(),
            1, // 1秒タイムアウト
            64, // 64MBメモリ制限
        ),
    ];

    let suite = TestSuite {
        source_file: output_path,
        test_cases,
        working_dir: Some(temp_dir.path().to_path_buf()),
    };

    // テストを実行
    let results = runner.run_suite("rust", &suite).await?;

    // 結果を検証
    for (i, result) in results.iter().enumerate() {
        assert!(
            result.success,
            "テストケース {} が失敗: {}",
            i + 1,
            result.error.as_deref().unwrap_or("不明なエラー")
        );
        println!(
            "テストケース {}: 実行時間 {}ms",
            i + 1,
            result.execution_time_ms
        );
    }

    Ok(())
}

#[tokio::test]
async fn test_timeout_process() -> Result<()> {
    let config = Config::get_default_config()?;
    let executor = ProcessExecutor::new(config);
    let runner = TestRunner::new(executor);

    // 無限ループのプログラム
    let source = r#"
fn main() {
    loop {
        std::thread::sleep(std::time::Duration::from_secs(1));
    }
}
"#;

    let temp_dir = tempfile::tempdir()?;
    let source_path = temp_dir.path().join("infinite.rs");
    std::fs::write(&source_path, source)?;

    let output_path = temp_dir.path().join("infinite");
    std::process::Command::new("rustc")
        .arg(&source_path)
        .arg("-o")
        .arg(&output_path)
        .output()?;

    let test_case = TestCase::with_limits(
        "".to_string(),
        "".to_string(),
        1, // 1秒タイムアウト
        64,
    );

    let suite = TestSuite {
        source_file: output_path,
        test_cases: vec![test_case],
        working_dir: Some(temp_dir.path().to_path_buf()),
    };

    let results = runner.run_suite("rust", &suite).await?;
    assert!(!results[0].success);
    assert!(results[0].error.as_ref().unwrap().contains("タイムアウト"));

    Ok(())
}

#[tokio::test]
async fn test_memory_limit() -> Result<()> {
    let config = Config::get_default_config()?;
    let executor = ProcessExecutor::new(config);
    let runner = TestRunner::new(executor);

    // メモリを大量に消費するプログラム
    let source = r#"
fn main() {
    let v: Vec<i32> = vec![0; 100_000_000]; // 約400MB
    println!("{}", v.len());
}
"#;

    let temp_dir = tempfile::tempdir()?;
    let source_path = temp_dir.path().join("memory.rs");
    std::fs::write(&source_path, source)?;

    let output_path = temp_dir.path().join("memory");
    std::process::Command::new("rustc")
        .arg(&source_path)
        .arg("-o")
        .arg(&output_path)
        .output()?;

    let test_case = TestCase::with_limits(
        "".to_string(),
        "100000000\n".to_string(),
        10,
        32, // 32MBメモリ制限
    );

    let suite = TestSuite {
        source_file: output_path,
        test_cases: vec![test_case],
        working_dir: Some(temp_dir.path().to_path_buf()),
    };

    let results = runner.run_suite("rust", &suite).await?;
    assert!(!results[0].success);
    assert!(results[0].error.as_ref().unwrap().contains("メモリ制限"));

    Ok(())
} 