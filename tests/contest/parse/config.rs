use anyhow::Result;
use cph::contest::parse::Config;

#[test]
fn test_config_loading() -> Result<()> {
    let config = Config::from_file("tests/contest/parse/test_commands.yaml")?;
    
    // サイトのエイリアス解決をテスト
    assert_eq!(
        config.resolve_alias("at"),
        Some(("site".to_string(), "atcoder".to_string()))
    );

    // 言語のエイリアス解決をテスト
    assert_eq!(
        config.resolve_alias("rs"),
        Some(("language".to_string(), "rust".to_string()))
    );

    // 存在しないエイリアスのテスト
    assert_eq!(config.resolve_alias("nonexistent"), None);

    Ok(())
} 