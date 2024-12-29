use std::error::Error;
use clap::{Command, ArgMatches};
use crate::alias::AliasManager;

pub type Result<T> = std::result::Result<T, Box<dyn Error>>;

/// CLIパーサー
pub struct CliParser {
    alias_manager: AliasManager,
}

impl CliParser {
    pub fn new(alias_manager: AliasManager) -> Self {
        Self { alias_manager }
    }

    /// コマンドライン引数を解析する
    pub fn parse(&self, args: Vec<String>) -> Result<ArgMatches> {
        // 最初の引数（プログラム名）以外を小文字に変換
        let args: Vec<String> = args.into_iter()
            .enumerate()
            .map(|(i, s)| if i == 0 { s } else { s.to_lowercase() })
            .collect();

        // サイトの解決
        let site = if args.len() > 1 {
            self.alias_manager.resolve("site", &args[1])?
        } else {
            return Err("サイトが指定されていません".into());
        };

        // コマンドの構築
        let cmd = self.build_cli();
        
        // 解決されたサイトを使用してコマンドを実行
        let mut args = args.clone();
        args[1] = site;
        
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
                    .subcommand_required(true)
                    .subcommands(self.common_subcommands())
            )
    }

    /// 共通のサブコマンドを構築する
    fn common_subcommands(&self) -> Vec<Command> {
        vec![
            Command::new("work")
                .about("コンテストのワークスペースを設定")
                .arg(clap::Arg::new("contest")
                    .help("コンテストID")
                    .required(true)),
            
            Command::new("test")
                .about("問題のテストを実行")
                .arg(clap::Arg::new("problem_id")
                    .help("問題ID")
                    .required(true)),
            
            Command::new("language")
                .about("使用する言語を設定")
                .arg(clap::Arg::new("language")
                    .help("プログラミング言語")
                    .required(true)),
        ]
    }
}
