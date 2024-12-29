use std::error::Error;
use clap::ArgMatches;

pub type Result<T> = std::result::Result<T, Box<dyn Error>>;

/// コマンドの基本トレイト
pub trait Command {
    /// コマンドを実行する
    fn execute(&self, matches: &ArgMatches) -> Result<()>;
}

/// コマンドのコンテキスト
pub struct CommandContext {
    pub site: String,
    pub workspace_path: std::path::PathBuf,
}

// 各コマンドのモジュール
pub mod work;
pub mod test;
pub mod language;

// 各コマンドの再エクスポート
pub use work::WorkCommand;
pub use test::TestCommand;
pub use language::LanguageCommand;
