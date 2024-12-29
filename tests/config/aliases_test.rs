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

#[test]
fn test_cli_edge_cases_args() {
    let config = AliasConfig::load("src/config/aliases.yaml").unwrap();

    // 空の引数
    let args = vec!["cph".to_string()];
    assert!(Cli::parse_from(args, config.clone()).is_err());

    // 引数の途中に空白を含む
    let args = vec![
        "cph".to_string(),
        "atcoder".to_string(),
        "test".to_string(),
        "abc 123".to_string(),
    ];
    let result = Cli::parse_from(args, config.clone());
    assert!(result.is_ok(), "空白を含む問題IDは許可すべき");

    // 非常に長い引数
    let long_arg = "a".repeat(1000);
    let args = vec![
        "cph".to_string(),
        "atcoder".to_string(),
        "test".to_string(),
        long_arg,
    ];
    let result = Cli::parse_from(args, config.clone());
    assert!(result.is_ok(), "長い引数は許可すべき");

    // 特殊文字を含む引数
    let special_chars = vec!["!@#$%^&*()", "../../test", "\"quoted\"", "\\escaped\\"];
    for special_char in special_chars {
        let args = vec![
            "cph".to_string(),
            "atcoder".to_string(),
            "test".to_string(),
            special_char.to_string(),
        ];
        let result = Cli::parse_from(args.clone(), config.clone());
        assert!(result.is_ok(), "特殊文字 {} を含む引数は許可すべき", special_char);
    }

    // 引数の順序が正しくない
    let args = vec![
        "cph".to_string(),
        "test".to_string(),  // サイトの前にコマンド
        "atcoder".to_string(),
    ];
    assert!(Cli::parse_from(args, config.clone()).is_err());

    // 重複した引数
    let args = vec![
        "cph".to_string(),
        "atcoder".to_string(),
        "test".to_string(),
        "a".to_string(),
        "a".to_string(),  // 同じ問題IDを重複して指定
    ];
    assert!(Cli::parse_from(args, config.clone()).is_err());

    // UTF-8の特殊文字
    let args = vec![
        "cph".to_string(),
        "atcoder".to_string(),
        "test".to_string(),
        "問題🎯".to_string(),
    ];
    let result = Cli::parse_from(args, config.clone());
    assert!(result.is_ok(), "UTF-8の特殊文字は許可すべき");
}

#[test]
fn test_cli_edge_cases_aliases() {
    let config = AliasConfig::load("src/config/aliases.yaml").unwrap();

    // 大文字小文字が混在するエイリアス
    let args = vec![
        "cph".to_string(),
        "AtCoder".to_string(),  // 大文字小文字が混在
        "Test".to_string(),     // 大文字小文字が混在
        "a".to_string(),
    ];
    let result = Cli::parse_from(args, config.clone());
    assert!(result.is_ok(), "大文字小文字の違いは無視されるべき");

    // エイリアスの連続使用
    let args = vec![
        "cph".to_string(),
        "ac".to_string(),       // atcoderのエイリアス
        "t".to_string(),        // testのエイリアス
        "a".to_string(),
    ];
    let result = Cli::parse_from(args, config.clone());
    assert!(result.is_ok(), "複数のエイリアスを連続して使用できるべき");

    // 存在しないエイリアスとコマンドの組み合わせ
    let invalid_combinations = vec![
        vec!["cph", "ac", "invalid"],           // 存在しないコマンド
        vec!["cph", "invalid", "test"],         // 存在しないサイト
        vec!["cph", "ac", "t", "a", "extra"],   // 余分な引数
    ];
    for args in invalid_combinations {
        let args: Vec<String> = args.into_iter().map(String::from).collect();
        assert!(Cli::parse_from(args, config.clone()).is_err());
    }

    // 部分一致するエイリアス
    let args = vec![
        "cph".to_string(),
        "atcode".to_string(),   // "atcoder"の部分文字列
        "test".to_string(),
        "a".to_string(),
    ];
    assert!(Cli::parse_from(args, config.clone()).is_err(), "部分一致するエイリアスは許可すべきでない");

    // エイリアスとコマンドの組み合わせ
    let valid_combinations = vec![
        vec!["cph", "ac", "t"],         // 両方エイリアス
        vec!["cph", "atcoder", "t"],    // サイトが正式名、コマンドがエイリアス
        vec!["cph", "ac", "test"],      // サイトがエイリアス、コマンドが正式名
    ];
    for combo in valid_combinations {
        let args: Vec<String> = combo.into_iter().map(String::from).collect();
        let result = Cli::parse_from(args.clone(), config.clone());
        assert!(result.is_ok(), "有効なエイリアスの組み合わせが失敗: {:?}", args);
    }
}

#[test]
fn test_cli_edge_cases_language() {
    let config = AliasConfig::load("src/config/aliases.yaml").unwrap();

    // 存在しない言語ID
    let args = vec![
        "cph".to_string(),
        "atcoder".to_string(),
        "language".to_string(),
        "invalid_lang".to_string(),
    ];
    assert!(Cli::parse_from(args, config.clone()).is_err());

    // 大文字小文字が混在する言語指定
    let valid_langs = vec![
        "Python", "PYTHON", "python",
        "Cpp", "CPP", "cpp",
        "Rust", "RUST", "rust",
    ];
    for lang in valid_langs {
        let args = vec![
            "cph".to_string(),
            "atcoder".to_string(),
            "language".to_string(),
            lang.to_string(),
        ];
        let result = Cli::parse_from(args.clone(), config.clone());
        assert!(result.is_ok(), "有効な言語指定が失敗: {}", lang);
    }

    // 特殊文字を含む言語指定
    let invalid_langs = vec![
        "python!", "c++", "rust-2021",
        "python3.9", "cpp-17", "rust_nightly",
    ];
    for lang in invalid_langs {
        let args = vec![
            "cph".to_string(),
            "atcoder".to_string(),
            "language".to_string(),
            lang.to_string(),
        ];
        let result = Cli::parse_from(args.clone(), config.clone());
        assert!(result.is_err(), "無効な言語指定が成功: {}", lang);
    }

    // 空の言語指定
    let args = vec![
        "cph".to_string(),
        "atcoder".to_string(),
        "language".to_string(),
        "".to_string(),
    ];
    assert!(Cli::parse_from(args, config.clone()).is_err());

    // 言語エイリアスの使用
    let alias_langs = vec![
        "py", "python3",    // Pythonのエイリアス
        "rs",               // Rustのエイリアス
    ];
    for lang in alias_langs {
        let args = vec![
            "cph".to_string(),
            "atcoder".to_string(),
            "language".to_string(),
            lang.to_string(),
        ];
        let result = Cli::parse_from(args.clone(), config.clone());
        assert!(result.is_ok(), "有効な言語エイリアスが失敗: {}", lang);
    }
}

#[test]
fn test_cli_edge_cases_ids() {
    let config = AliasConfig::load("src/config/aliases.yaml").unwrap();

    // コンテストIDのテスト
    let contest_cases = vec![
        // 有効なケース
        ("abc123", true),
        ("arc123", true),
        ("agc123", true),
        // 無効なケース
        ("", false),
        ("abc", false),        // 数字なし
        ("123", false),        // プレフィックスなし
        ("abc-123", false),    // ハイフンを含む
        ("abc_123", false),    // アンダースコアを含む
        ("abc123a", false),    // 数字の後に文字
    ];

    for (contest_id, should_pass) in contest_cases {
        let args = vec![
            "cph".to_string(),
            "atcoder".to_string(),
            "work".to_string(),
            contest_id.to_string(),
        ];
        let result = Cli::parse_from(args.clone(), config.clone());
        assert_eq!(
            result.is_ok(),
            should_pass,
            "コンテストID '{}' のテストが失敗",
            contest_id
        );
    }

    // 問題IDのテスト
    let problem_cases = vec![
        // 有効なケース
        ("a", true),
        ("b", true),
        ("c", true),
        ("d", true),
        ("e", true),
        ("f", true),
        ("g", true),
        ("ex", true),
        // 無効なケース
        ("", false),
        ("1", false),         // 数字のみ
        ("aa", false),        // 2文字
        ("A", false),         // 大文字
        ("h", false),         // 範囲外
        ("z", false),         // 範囲外
        ("-a", false),        // 特殊文字
        ("a-", false),        // 特殊文字
    ];

    for (problem_id, should_pass) in problem_cases {
        let args = vec![
            "cph".to_string(),
            "atcoder".to_string(),
            "test".to_string(),
            problem_id.to_string(),
        ];
        let result = Cli::parse_from(args.clone(), config.clone());
        assert_eq!(
            result.is_ok(),
            should_pass,
            "問題ID '{}' のテストが失敗",
            problem_id
        );
    }

    // 問題IDとコンテストIDの組み合わせ
    let combined_cases = vec![
        // 有効なケース
        (("abc123", "a"), true),
        (("arc123", "c"), true),
        // 無効なケース
        (("abc123", "x"), false),    // 無効な問題ID
        (("invalid", "a"), false),   // 無効なコンテストID
    ];

    for ((contest_id, problem_id), should_pass) in combined_cases {
        let args = vec![
            "cph".to_string(),
            "atcoder".to_string(),
            "work".to_string(),
            contest_id.to_string(),
        ];
        let result1 = Cli::parse_from(args.clone(), config.clone());

        let args = vec![
            "cph".to_string(),
            "atcoder".to_string(),
            "test".to_string(),
            problem_id.to_string(),
        ];
        let result2 = Cli::parse_from(args.clone(), config.clone());

        assert_eq!(
            result1.is_ok() && result2.is_ok(),
            should_pass,
            "コンテストID '{}' と問題ID '{}' の組み合わせテストが失敗",
            contest_id,
            problem_id
        );
    }
} 