use clap::{Parser, Subcommand};
use serde::{Serialize, Deserialize};

#[derive(Debug, Parser)]
#[command(author, version, about, long_about = None)]
pub struct Cli {
    /// サイト名
    #[arg(value_enum)]
    pub site: Site,

    /// サブコマンド
    #[command(subcommand)]
    pub command: Commands,
}

#[derive(Debug, Clone, clap::ValueEnum, Serialize, Deserialize)]
pub enum Site {
    /// AtCoder
    AtCoder,
}

impl Site {
    pub fn get_url(&self) -> &'static str {
        match self {
            Site::AtCoder => "https://atcoder.jp",
        }
    }

    pub fn get_name(&self) -> &'static str {
        match self {
            Site::AtCoder => "AtCoder",
        }
    }
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

pub mod commands;
