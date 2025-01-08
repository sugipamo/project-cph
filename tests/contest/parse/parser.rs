use anyhow::Result;
use cph::contest::model::Command;
use cph::contest::parse::{Parser, Config};

fn create_test_parser() -> Parser {
    let config = Config::from_file("tests/contest/parse/test_commands.yaml").unwrap();
    Parser::with_config(config)
}

#[test]
fn test_basic_parsing() -> Result<()> {
    let parser = create_test_parser();
    
    // 基本的なパースのテスト
    let context = parser.parse("abc123 a")?;
    assert_eq!(
        context.command,
        Command::Open {
            site: None,
            contest_id: Some("abc123".to_string()),
            problem_id: Some("a".to_string()),
            language: None,
        }
    );

    // サイトとコンテストIDのテスト
    let context = parser.parse("atcoder abc123")?;
    assert_eq!(
        context.command,
        Command::Open {
            site: Some("atcoder".to_string()),
            contest_id: Some("abc123".to_string()),
            problem_id: None,
            language: None,
        }
    );

    // 全パラメータのテスト
    let context = parser.parse("atcoder abc123 a rust")?;
    assert_eq!(
        context.command,
        Command::Open {
            site: Some("atcoder".to_string()),
            contest_id: Some("abc123".to_string()),
            problem_id: Some("a".to_string()),
            language: Some("rust".to_string()),
        }
    );

    Ok(())
}

#[test]
fn test_alias_resolution() -> Result<()> {
    let parser = create_test_parser();
    
    // サイトのエイリアス解決
    let context = parser.parse("at abc123")?;
    assert_eq!(
        context.command,
        Command::Open {
            site: Some("atcoder".to_string()),
            contest_id: Some("abc123".to_string()),
            problem_id: None,
            language: None,
        }
    );

    // 言語のエイリアス解決
    let context = parser.parse("abc123 a rs")?;
    assert_eq!(
        context.command,
        Command::Open {
            site: None,
            contest_id: Some("abc123".to_string()),
            problem_id: Some("a".to_string()),
            language: Some("rust".to_string()),
        }
    );

    Ok(())
}

#[test]
fn test_error_cases() -> Result<()> {
    let parser = create_test_parser();
    
    // 空入力のテスト
    assert!(parser.parse("").is_err());
    assert!(parser.parse("   ").is_err());

    Ok(())
} 