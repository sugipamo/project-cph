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

    // サイトとproblem_idのテスト
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
fn test_complex_patterns() -> Result<()> {
    let parser = create_test_parser();

    // 複数の問題ID候補がある場合
    let context = parser.parse("abc123 a b c")?;
    assert_eq!(
        context.command,
        Command::Open {
            site: None,
            contest_id: Some("abc123".to_string()),
            problem_id: Some("a".to_string()),  // 最初の値を問題IDとして解釈
            language: None,
        }
    );

    // 順序が異なる場合
    let context = parser.parse("rs abc123 atcoder a")?;
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
fn test_edge_cases() -> Result<()> {
    let parser = create_test_parser();

    // 最小限の入力
    let context = parser.parse("abc123")?;
    assert_eq!(
        context.command,
        Command::Open {
            site: None,
            contest_id: Some("abc123".to_string()),
            problem_id: None,
            language: None,
        }
    );

    // サイトのみの入力
    let context = parser.parse("atcoder")?;
    assert_eq!(
        context.command,
        Command::Open {
            site: Some("atcoder".to_string()),
            contest_id: None,
            problem_id: None,
            language: None,
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

    // 余分な空白を含む入力
    let context = parser.parse("  abc123   a  ")?;
    assert_eq!(
        context.command,
        Command::Open {
            site: None,
            contest_id: Some("abc123".to_string()),
            problem_id: Some("a".to_string()),
            language: None,
        }
    );

    Ok(())
}

#[test]
fn test_priority_handling() -> Result<()> {
    let parser = create_test_parser();

    // イトと1つのトークン
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

    Ok(())
}

#[test]
fn test_invalid_config() -> Result<()> {
    // 無効な設定ファイルの読み込み
    let config = Config::from_file("tests/contest/parse/invalid_commands.yaml")?;
    
    // 空白を含むエイリアスが無視されていることを確認
    assert!(!config.resolve_alias("at test").is_some());
    assert!(!config.resolve_alias("at coder").is_some());
    assert!(!config.resolve_alias("cf test").is_some());
    assert!(!config.resolve_alias("code forces").is_some());
    assert!(!config.resolve_alias("rust 2021").is_some());
    assert!(!config.resolve_alias("rs test").is_some());

    // 存在しない設定ファイル
    let result = Config::from_file("nonexistent.yaml");
    assert!(result.is_err());

    Ok(())
}

#[test]
fn test_special_characters() -> Result<()> {
    let config = Config::from_file("tests/contest/parse/special_commands.yaml")?;
    let parser = Parser::with_config(config);

    // ハイフンを含むエイリアス
    let context = parser.parse("at-test abc123")?;
    assert_eq!(
        context.command,
        Command::Open {
            site: Some("atcoder-test".to_string()),
            contest_id: Some("abc123".to_string()),
            problem_id: None,
            language: None,
        }
    );

    // 空白を含むエイリアス
    let context = parser.parse("at test abc123")?;
    assert_eq!(
        context.command,
        Command::Open {
            site: None,
            contest_id: Some("at".to_string()),
            problem_id: Some("test".to_string()),
            language: None,
        }
    );

    // Unicode文字
    let context = parser.parse("ユ abc123")?;
    assert_eq!(
        context.command,
        Command::Open {
            site: Some("ユーコーダー".to_string()),
            contest_id: Some("abc123".to_string()),
            problem_id: None,
            language: None,
        }
    );

    Ok(())
}

#[test]
fn test_performance() -> Result<()> {
    let parser = create_test_parser();
    
    // 長い入力のテスト
    let long_input = "atcoder abc123 a rust ".repeat(100);
    let context = parser.parse(&long_input)?;
    assert_eq!(
        context.command,
        Command::Open {
            site: Some("atcoder".to_string()),
            contest_id: Some("abc123".to_string()),
            problem_id: Some("a".to_string()),
            language: Some("rust".to_string()),
        }
    );

    // 多数のトークンを含む入力
    let many_tokens = "abc123 a b c d e f g h i j k l m n o p".to_string();
    let context = parser.parse(&many_tokens)?;
    assert_eq!(
        context.command,
        Command::Open {
            site: None,
            contest_id: Some("abc123".to_string()),
            problem_id: Some("a".to_string()),
            language: None,
        }
    );

    Ok(())
}

#[test]
fn test_whitespace_handling() -> Result<()> {
    let parser = create_test_parser();

    // タブを含む入力
    let context = parser.parse("atcoder\tabc123\ta\trust")?;
    assert_eq!(
        context.command,
        Command::Open {
            site: Some("atcoder".to_string()),
            contest_id: Some("abc123".to_string()),
            problem_id: Some("a".to_string()),
            language: Some("rust".to_string()),
        }
    );

    // 複数の連続した空白
    let context = parser.parse("atcoder    abc123  a    rust")?;
    assert_eq!(
        context.command,
        Command::Open {
            site: Some("atcoder".to_string()),
            contest_id: Some("abc123".to_string()),
            problem_id: Some("a".to_string()),
            language: Some("rust".to_string()),
        }
    );

    // 前後の空白
    let context = parser.parse("   atcoder abc123 a rust   ")?;
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
fn test_problem_id_priority() -> Result<()> {
    let parser = create_test_parser();

    // 一のトークンはcontest_idとして解釈
    let context = parser.parse("at a")?;
    assert_eq!(
        context.command,
        Command::Open {
            site: Some("atcoder".to_string()),
            contest_id: Some("a".to_string()),
            problem_id: None,
            language: None,
        }
    );

    Ok(())
}

#[test]
fn test_token_interpretation() -> Result<()> {
    let parser = create_test_parser();

    // 単一のトークンはcontest_idとして解釈
    let context = parser.parse("aaa")?;
    assert_eq!(
        context.command,
        Command::Open {
            site: None,
            contest_id: Some("aaa".to_string()),
            problem_id: None,
            language: None,
        }
    );

    Ok(())
} 