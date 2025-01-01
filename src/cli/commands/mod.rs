use std::error::Error;
use crate::cli::Commands;

pub type Result<T> = std::result::Result<T, Box<dyn Error>>;

/// コマンドの基本トレイト
#[async_trait::async_trait]
pub trait Command {
    /// コマンドを実行する
    /// 
    /// # エラーハンドリング
    /// - 重大なエラーのみ`Err`を返す
    /// - 軽微なエラーは`println!`で報告し、`Ok(())`を返す
    async fn execute(&self, command: &Commands) -> Result<()>;
}

/// コマンドのコンテキスト
pub struct CommandContext {
    pub site_id: String,
    pub problem_id: String,
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
        "work" => Some(Box::new(WorkCommand::new(context.problem_id.clone()))),
        "test" => Some(Box::new(TestCommand::new(context))),
        "language" => Some(Box::new(LanguageCommand::new(context))),
        "open" => Some(Box::new(OpenCommand::new(context.site_id.clone(), context.problem_id.clone()))),
        "submit" => Some(Box::new(SubmitCommand::new(context.site_id.clone(), context.problem_id.clone()))),
        "generate" => Some(Box::new(GenerateCommand::new(context))),
        "login" => Some(Box::new(LoginCommand::new(context.site_id.clone()))),
        _ => None,
    }
}
