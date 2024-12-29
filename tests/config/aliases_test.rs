#[cfg(test)]
use cph::{
    config::aliases::AliasConfig,
    cli::{CliParser, Cli, Site, CommonSubCommand},
};

#[test]
fn test_resolve_language() {
    let config = AliasConfig::load("src/config/aliases.yaml").unwrap();
    
    // Python
    assert_eq!(config.resolve_language("python"), Some("python".to_string()));
    assert_eq!(config.resolve_language("Python"), Some("python".to_string()));
    assert_eq!(config.resolve_language("python3"), Some("python".to_string()));
    
    // PyPy
    assert_eq!(config.resolve_language("pypy"), Some("pypy".to_string()));
    assert_eq!(config.resolve_language("PyPy"), Some("pypy".to_string()));
    assert_eq!(config.resolve_language("pypy3"), Some("pypy".to_string()));
    assert_eq!(config.resolve_language("py"), Some("pypy".to_string()));
    
    // 存在しない言語
    assert_eq!(config.resolve_language("invalid"), None);
}

#[test]
fn test_resolve_command() {
    let config = AliasConfig::load("src/config/aliases.yaml").unwrap();
    
    // test command
    assert_eq!(config.resolve_command("test"), Some("test".to_string()));
    assert_eq!(config.resolve_command("t"), Some("test".to_string()));
    assert_eq!(config.resolve_command("check"), Some("test".to_string()));
    
    // language command
    assert_eq!(config.resolve_command("language"), Some("language".to_string()));
    assert_eq!(config.resolve_command("l"), Some("language".to_string()));
    assert_eq!(config.resolve_command("lang"), Some("language".to_string()));
    
    // login command
    assert_eq!(config.resolve_command("login"), Some("login".to_string()));
    assert_eq!(config.resolve_command("auth"), Some("login".to_string()));
    
    // 存在しないコマンド
    assert_eq!(config.resolve_command("invalid"), None);
}

#[test]
fn test_resolve_site() {
    let config = AliasConfig::load("src/config/aliases.yaml").unwrap();
    
    // AtCoder
    assert_eq!(config.resolve_site("atcoder"), Some("atcoder".to_string()));
    assert_eq!(config.resolve_site("at-coder"), Some("atcoder".to_string()));
    assert_eq!(config.resolve_site("at_coder"), Some("atcoder".to_string()));
    assert_eq!(config.resolve_site("AtCoder"), Some("atcoder".to_string()));
    assert_eq!(config.resolve_site("ac"), Some("atcoder".to_string()));
    
    // 存在しないサイト
    assert_eq!(config.resolve_site("invalid"), None);
}

#[test]
fn test_resolve_command_with_args() {
    let config = AliasConfig::load("src/config/aliases.yaml").unwrap();
    
    // 基本的なコマンド解決
    assert_eq!(
        config.resolve_command_with_args("t", vec!["abc001".to_string()]),
        Some(("test".to_string(), vec!["abc001".to_string()]))
    );

    // 引数なしのコマンド
    assert_eq!(
        config.resolve_command_with_args("l", vec![]),
        Some(("language".to_string(), vec![]))
    );

    // 存在しないコマンド
    assert_eq!(
        config.resolve_command_with_args("invalid", vec![]),
        None
    );
}

#[test]
fn test_resolve_args() {
    let config = AliasConfig::load("src/config/aliases.yaml").unwrap();
    
    // プログラム名のみ
    assert_eq!(
        config.resolve_args(vec!["cph".to_string()]),
        Some(vec!["cph".to_string()])
    );

    // コマンドとサブコマンドの解決
    assert_eq!(
        config.resolve_args(vec![
            "cph".to_string(),
            "t".to_string(),
            "abc001".to_string()
        ]),
        Some(vec![
            "cph".to_string(),
            "test".to_string(),
            "abc001".to_string()
        ])
    );

    // 複数のエイリアスを含むコマンド
    assert_eq!(
        config.resolve_args(vec![
            "cph".to_string(),
            "l".to_string(),
            "py".to_string()
        ]),
        Some(vec![
            "cph".to_string(),
            "language".to_string(),
            "py".to_string()
        ])
    );
}

#[test]
fn test_cli_parser() {
    let config = AliasConfig::load("src/config/aliases.yaml").unwrap();
    let parser = CliParser::new(config);

    // 基本的なコマンド
    let args = vec![
        "cph".to_string(),
        "atcoder".to_string(),
        "test".to_string(),
        "a".to_string(),
    ];
    let matches = parser.parse_from_args(args).unwrap();
    assert!(matches.subcommand_matches("atcoder").is_some());

    // エイリアスを使用したコマンド
    let args = vec![
        "cph".to_string(),
        "at-coder".to_string(),
        "t".to_string(),
        "b".to_string(),
    ];
    let matches = parser.parse_from_args(args).unwrap();
    assert!(matches.subcommand_matches("atcoder").is_some());

    // 無効なコマンド
    let args = vec![
        "cph".to_string(),
        "invalid".to_string(),
        "test".to_string(),
    ];
    assert!(parser.parse_from_args(args).is_err());
}

#[test]
fn test_cli_parse_from() {
    let config = AliasConfig::load("src/config/aliases.yaml").unwrap();

    // 基本的なコマンド
    let args = vec![
        "cph".to_string(),
        "atcoder".to_string(),
        "test".to_string(),
        "a".to_string(),
    ];
    let cli = Cli::parse_from(args, config.clone()).unwrap();
    match cli.site {
        Site::AtCoder { command } => match command {
            CommonSubCommand::Test { problem_id } => assert_eq!(problem_id, "a"),
            _ => panic!("Expected Test command"),
        },
    }

    // エイリアスを使用したコマンド
    let args = vec![
        "cph".to_string(),
        "at-coder".to_string(),
        "t".to_string(),
        "b".to_string(),
    ];
    let cli = Cli::parse_from(args, config.clone()).unwrap();
    match cli.site {
        Site::AtCoder { command } => match command {
            CommonSubCommand::Test { problem_id } => assert_eq!(problem_id, "b"),
            _ => panic!("Expected Test command"),
        },
    }

    // 無効なコマンド
    let args = vec![
        "cph".to_string(),
        "invalid".to_string(),
        "test".to_string(),
    ];
    assert!(Cli::parse_from(args, config.clone()).is_err());

    // 必須引数の欠落
    let args = vec![
        "cph".to_string(),
        "atcoder".to_string(),
        "test".to_string(),
    ];
    assert!(Cli::parse_from(args, config).is_err());
} 