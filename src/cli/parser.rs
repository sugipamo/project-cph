use std::error::Error;
use clap::{Command, ArgMatches, Arg};
use crate::config::{self, LanguageConfig};
use clap::{Parser, Subcommand};
use crate::config::languages::{DEFAULT_SOURCE_NAME, SOURCE_NAME_ENV_KEY};

pub type Result<T> = std::result::Result<T, Box<dyn Error>>;

/// CLIパーサー
pub struct CliParser {
    lang_config: LanguageConfig,
}

impl CliParser {
    pub fn new() -> Result<Self> {
        println!("設定を読み込んでいます...");
        let config_paths = config::get_config_paths();
        let lang_config = LanguageConfig::load(config_paths.languages)?;
        Ok(Self { lang_config })
    }

    /// コマンドライン引数を解析する
    pub fn parse(&self, args: Vec<String>) -> Result<ArgMatches> {
        // 最初の引数（プログラム名）以外を小文字に変換
        let args: Vec<String> = args.into_iter()
            .enumerate()
            .map(|(i, s)| if i == 0 { s } else { s.to_lowercase() })
            .collect();

        // サイトの検証
        let site = if args.len() > 1 {
            match args[1].as_str() {
                "atcoder" => "atcoder",
                _ => return Err("サポートされていないサイトです".into()),
            }
        } else {
            return Err("サイトが指定されていません".into());
        };

        // コマンドの構築
        let cmd = self.build_cli();
        
        // 解決されたサイトを使用してコマンドを実行
        let mut args = args.clone();
        args[1] = site.to_string();
        
        cmd.try_get_matches_from(args)
            .map_err(|e| e.into())
    }

    /// CLIの構造を構築する
    fn build_cli(&self) -> Command {
        Command::new("cph")
            .about("競技プログラミングヘルパー")
            .subcommand_required(true)
            .subcommand(
                Command::new("atcoder")
                    .about("AtCoder関連のコマンド")
                    .subcommands(self.common_subcommands())
            )
    }

    /// 共通のサブコマンドを構築する
    fn common_subcommands(&self) -> Vec<Command> {
        let languages: Vec<String> = self.lang_config.list_languages();
        println!("利用可能な言語: {:?}", languages);

        vec![
            Command::new("work")
                .about("コンテストの作業ディレクトリを設定")
                .arg(Arg::new("contest_id")
                    .help("コンテストID")
                    .required(true)),

            Command::new("test")
                .about("テストを実行")
                .arg(Arg::new("problem_id")
                    .help("問題ID")
                    .required(true)),

            Command::new("language")
                .about("使用する言語を設定")
                .arg(Arg::new("language")
                    .help("プログラミング言語")
                    .required(true)
                    .value_parser(languages)),

            Command::new("open")
                .about("問題ページを開く")
                .arg(Arg::new("problem_id")
                    .help("問題ID")
                    .required(true)),

            Command::new("submit")
                .about("解答を提出")
                .arg(Arg::new("problem_id")
                    .help("問題ID")
                    .required(true)),

            Command::new("generate")
                .about("ソースファイルを生成")
                .arg(Arg::new("problem_id")
                    .help("問題ID")
                    .required(true)),

            Command::new("login")
                .about("サイトにログイン"),
        ]
    }
}

#[derive(Parser, Debug)]
#[command(author, version, about, long_about = None)]
pub struct Cli {
    #[clap(long, env = SOURCE_NAME_ENV_KEY, default_value = DEFAULT_SOURCE_NAME, help = "ソースファイルのベース名")]
    pub source: String,

    #[command(subcommand)]
    pub command: Commands,
}
