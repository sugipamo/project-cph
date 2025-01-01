use clap::{Parser, Subcommand};

#[derive(Debug, Parser)]
#[command(author, version, about, long_about = None)]
pub struct Cli {
    /// サイト名（例: atcoder）
    #[arg(global = true, short = 's', long = "site", default_value = "atcoder")]
    pub site_id: String,

    /// サブコマンド
    #[command(subcommand)]
    pub command: Commands,
}

#[derive(Debug, Subcommand)]
pub enum Commands {
    /// ログイン
    Login,
    
    /// コンテストの設定
    #[command(alias = "w")]
    Work {
        /// コンテストID
        contest_id: String,
    },

    /// 問題を開く
    #[command(alias = "o")]
    Open {
        /// 問題ID
        problem_id: String,
    },

    /// 言語の設定
    #[command(alias = "l")]
    Language {
        /// 言語
        language: String,
    },

    /// テストを実行
    #[command(alias = "t")]
    Test {
        /// 問題ID
        problem_id: String,
    },

    /// 解答を提出
    #[command(alias = "s")]
    Submit {
        /// 問題ID
        problem_id: String,
    },

    /// テストケースを生成
    #[command(alias = "g")]
    Generate {
        /// 問題ID
        problem_id: String,
    },
}

impl Commands {
    pub fn as_str(&self) -> &'static str {
        match self {
            Commands::Login => "login",
            Commands::Work { .. } => "work",
            Commands::Open { .. } => "open",
            Commands::Language { .. } => "language",
            Commands::Test { .. } => "test",
            Commands::Submit { .. } => "submit",
            Commands::Generate { .. } => "generate",
        }
    }
}

pub mod commands;
