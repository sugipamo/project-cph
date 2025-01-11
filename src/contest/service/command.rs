use crate::contest::model::{Command, CommandContext, Contest};
use crate::contest::service::{ContestHandler, TestRunner};
use anyhow::Result;
use crate::message::contest;

#[derive(Default)]
pub struct Service {
    #[allow(dead_code)]
    contest_service: ContestHandler,
    #[allow(dead_code)]
    test_service: TestRunner,
}

impl Service {
    /// `CommandService`の新しいインスタンスを作成します
    /// 
    /// # Errors
    /// 
    /// - 設定ファイルの読み込みに失敗した場合
    pub const fn new(contest_service: ContestHandler, test_service: TestRunner) -> Result<Self> {
        Ok(Self {
            contest_service,
            test_service,
        })
    }

    /// コマンドを実行します。
    /// 
    /// # Errors
    /// - コマンドの実行に失敗した場合
    /// - コンテストが選択されていない場合（必要な場合）
    pub fn execute(&self, context: CommandContext) -> Result<()> {
        match context.command {
            Command::Login => {
                println!("ログイン処理を実行します");
                // TODO: ログイン処理の実装
                Ok(())
            }
            Command::Config { site, contest_id, problem_id, language: _ } => {
                println!("問題を開きます: site={site:?}, contest={contest_id:?}, problem={problem_id:?}");
                site.map_or_else(
                    || Err(anyhow::anyhow!(contest::error("invalid_command", "サイトが指定されていません"))),
                    |_site_str| {
                        // TODO: Config実装完了後に修正
                        Ok(())
                    }
                )
            }
            Command::Open => {
                println!("問題を開きます");
                Ok(())
            }
            Command::Test { test_number } => {
                context.contest.map_or_else(
                    || Err(anyhow::anyhow!(contest::error("invalid_command", "コンテストが選択されていません"))),
                    |_contest| {
                        println!("テストを実行します: test_number={test_number:?}");
                        // TODO: Config実装完了後に修正
                        Ok(())
                    }
                )
            }
            Command::Submit => {
                context.contest.map_or_else(
                    || Err(anyhow::anyhow!(contest::error("invalid_command", "コンテストが選択されていません"))),
                    |_contest| {
                        println!("提出を行います");
                        // TODO: Config実装完了後に修正
                        Ok(())
                    }
                )
            }
        }
    }

    #[must_use = "この関数は新しいCommandContextインスタンスを返します"]
    pub const fn with_contest(&self, command: Command, contest: Contest) -> CommandContext {
        CommandContext::with_contest(command, contest)
    }

    #[must_use = "この関数は新しいCommandContextインスタンスを返します"]
    pub const fn without_contest(&self, command: Command) -> CommandContext {
        CommandContext::new(command)
    }
} 