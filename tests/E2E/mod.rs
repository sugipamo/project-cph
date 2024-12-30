use std::path::PathBuf;
use assert_cmd::Command;
use predicates::prelude::*;
use tokio;

mod helpers;
mod mocks;

use helpers::{
    setup_test_environment,
    setup_test_templates,
    verify_directory_structure,
    verify_file_contents,
    verify_command_result,
};
use mocks::{AtCoderMock, TestDockerRunner};

/// AtCoderのワークフローをテストする
#[tokio::test]
async fn test_atcoder_workflow() {
    // テスト環境のセットアップ
    let test_dir = setup_test_environment().await;
    setup_test_templates(&test_dir).await;

    // モックサーバーの起動
    let mock_server = AtCoderMock::start().await;
    let contest_id = "abc300";
    let problem_id = "a";

    // workコマンドのテスト
    let result = Command::cargo_bin("cph")
        .unwrap()
        .args(&["atcoder", "work", contest_id])
        .current_dir(&test_dir)
        .assert()
        .success();

    // ディレクトリ構造の検証
    verify_directory_structure(&test_dir, contest_id).await;

    // 設定ファイルの検証
    let contests_yaml = test_dir.join("active_contest/contests.yaml");
    let expected_content = format!(r#"
contest:
  id: "{}"
  site: "atcoder"
  url: "https://atcoder.jp/contests/{}"
"#, contest_id, contest_id);
    verify_file_contents(&contests_yaml, &expected_content).await;

    // openコマンドのテスト
    mock_server.mock_problem_page(contest_id, problem_id).await;
    let result = Command::cargo_bin("cph")
        .unwrap()
        .args(&["atcoder", "open", problem_id])
        .current_dir(&test_dir)
        .assert()
        .success();

    // ソースファイルの検証
    let source_file = test_dir.join("active_contest").join(format!("{}.rs", problem_id));
    assert!(source_file.exists(), "ソースファイルが作成されていません");

    // submitコマンドのテスト
    // テストケースの設定
    let mut docker_runner = TestDockerRunner::new(test_dir.clone());
    docker_runner.set_test_case("1\n", "2\n");

    // 提出のモック
    mock_server.mock_login().await;
    mock_server.mock_submit(contest_id, problem_id).await;

    let result = Command::cargo_bin("cph")
        .unwrap()
        .args(&["atcoder", "submit", problem_id])
        .current_dir(&test_dir)
        .assert()
        .success();

    // クリーンアップ
    cleanup_test_environment(test_dir).await;
}

/// エラーケースのテスト
#[tokio::test]
async fn test_atcoder_error_cases() {
    // テスト環境のセットアップ
    let test_dir = setup_test_environment().await;
    setup_test_templates(&test_dir).await;

    // モックサーバーの起動
    let mock_server = AtCoderMock::start().await;

    // 無効なコンテストIDのテスト
    let result = Command::cargo_bin("cph")
        .unwrap()
        .args(&["atcoder", "work", "invalid-contest-id"])
        .current_dir(&test_dir)
        .assert()
        .failure()
        .stderr(predicate::str::contains("無効なコンテストIDです"));

    // 存在しない問題のテスト
    let contest_id = "abc300";
    Command::cargo_bin("cph")
        .unwrap()
        .args(&["atcoder", "work", contest_id])
        .current_dir(&test_dir)
        .assert()
        .success();

    let result = Command::cargo_bin("cph")
        .unwrap()
        .args(&["atcoder", "open", "invalid-problem"])
        .current_dir(&test_dir)
        .assert()
        .failure()
        .stderr(predicate::str::contains("無効な問題IDです"));

    // 提出失敗のテスト
    mock_server.mock_error("/contests/abc300/submit", 400, "提出に失敗しました").await;
    let result = Command::cargo_bin("cph")
        .unwrap()
        .args(&["atcoder", "submit", "a"])
        .current_dir(&test_dir)
        .assert()
        .failure()
        .stderr(predicate::str::contains("提出に失敗しました"));

    // クリーンアップ
    cleanup_test_environment(test_dir).await;
}

/// テスト環境のクリーンアップ
async fn cleanup_test_environment(test_dir: PathBuf) {
    if test_dir.exists() {
        tokio::fs::remove_dir_all(test_dir)
            .await
            .expect("テストディレクトリの削除に失敗しました");
    }
} 