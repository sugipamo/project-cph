use anyhow::Error;

#[test]
fn test_error_conversion() {
    let err = Error::msg("テストエラー");
    assert!(err.to_string().contains("テストエラー"));
} 