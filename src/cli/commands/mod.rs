use std::error::Error;
use std::path::PathBuf;
use clap::ArgMatches;

pub type Result<T> = std::result::Result<T, Box<dyn Error>>;

/// コマンドの基本トレイト
pub trait Command {
    /// コマンドを実行する
    fn execute(&self, matches: &ArgMatches) -> Result<()>;
}

/// コマンドのコンテキスト
pub struct CommandContext {
    pub site: crate::cli::Site,
    pub workspace_path: PathBuf,
}

// 各コマンドのモジュール
pub mod work;
pub mod test;
pub mod language;
pub mod open;
pub mod submit;
pub mod generate;
pub mod login;

// 各コマンドの再エクスポート
pub use work::WorkCommand;
pub use test::TestCommand;
pub use language::LanguageCommand;
pub use open::OpenCommand;
pub use submit::SubmitCommand;
pub use generate::GenerateCommand;
pub use login::LoginCommand;

/// コマンドを生成する
pub fn create_command(name: &str, context: CommandContext) -> Option<Box<dyn Command>> {
    match name {
        "work" => Some(Box::new(WorkCommand::new(context))),
        "test" => Some(Box::new(TestCommand::new(context))),
        "language" => Some(Box::new(LanguageCommand::new(context))),
        "open" => Some(Box::new(OpenCommand::new(context))),
        "submit" => Some(Box::new(SubmitCommand::new(context))),
        "generate" => Some(Box::new(GenerateCommand::new(context))),
        "login" => Some(Box::new(LoginCommand::new(context))),
        _ => None,
    }
}
