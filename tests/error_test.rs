use cph::contest::error::{ContestError, ErrorContext};
use std::path::PathBuf;

#[test]
fn test_error_context() {
    let error = ContestError::Config {
        message: "設定の読み込みに失敗".to_string(),
        source: None,
    }
    .with_context("設定ファイルの読み込み", "config.yaml")
    .add_hint("設定ファイルの形式を確認してください");

    match error {
        ContestError::Config { message, source: _ } => {
            assert!(message.contains("設定の読み込みに失敗"));
            assert!(message.contains("操作: 設定ファイルの読み込み"));
            assert!(message.contains("場所: config.yaml"));
            assert!(message.contains("ヒント: 設定ファイルの形式を確認してください"));
        }
        _ => panic!("unexpected error variant"),
    }
}

#[test]
fn test_error_context_with_stack_trace() {
    let context = ErrorContext::new("テスト操作", "テスト場所")
        .with_hint("テストヒント")
        .with_stack_trace();

    assert_eq!(context.operation, "テスト操作");
    assert_eq!(context.location, "テスト場所");
    assert!(context.details.contains_key("hint"));
    assert_eq!(context.details.get("hint").unwrap(), "テストヒント");

    #[cfg(debug_assertions)]
    {
        assert!(context.details.contains_key("stack_trace"));
        assert!(!context.details.get("stack_trace").unwrap().is_empty());
    }

    #[cfg(not(debug_assertions))]
    {
        assert!(!context.details.contains_key("stack_trace"));
    }
}

#[test]
fn test_filesystem_error_context() {
    let path = PathBuf::from("test.txt");
    let error = ContestError::FileSystem {
        message: "ファイルの作成に失敗".to_string(),
        source: std::io::Error::new(std::io::ErrorKind::Other, "テストエラー"),
        path: path.clone(),
    }
    .with_context("ファイル作成", "test.txt")
    .add_hint("ファイルの権限を確認してください");

    match error {
        ContestError::FileSystem { message, source: _, path: error_path } => {
            assert!(message.contains("ファイルの作成に失敗"));
            assert!(message.contains("操作: ファイル作成"));
            assert!(message.contains("場所: test.txt"));
            assert!(message.contains("ヒント: ファイルの権限を確認してください"));
            assert_eq!(error_path, path);
        }
        _ => panic!("unexpected error variant"),
    }
} 