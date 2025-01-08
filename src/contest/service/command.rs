use crate::contest::model::{Command, CommandContext, Contest};
use crate::contest::service::{ContestService, TestService};
use anyhow::Result;

pub struct Service {
    contest_service: ContestService,
    test_service: TestService,
}

impl Service {
    #[must_use = "この関数は新しいCommandServiceインスタンスを返します"]
    pub const fn new(contest_service: ContestService, test_service: TestService) -> Self {
        Self {
            contest_service,
            test_service,
        }
    }

    /// コマンドを実行します。
    /// 
    /// # Errors
    /// - コマンドの実行に失敗した場合
    /// - コンテストが選択されていない場合（必要な場合）
    pub fn execute(&self, context: CommandContext) -> Result<()> {
        match context.command {
            Command::Login => {
                // TODO: ログイン処理の実装
                println!("ログイン処理を実行します");
                Ok(())
            }
            Command::Open { site, contest_id, problem_id } => {
                println!("問題を開きます: site={site}, contest={contest_id:?}, problem={problem_id:?}");
                self.contest_service.open(site, contest_id, problem_id)
            }
            Command::Test { test_number } => {
                context.contest.map_or_else(
                    || Err(anyhow::anyhow!("コンテストが選択されていません")),
                    |contest| {
                        println!("テストを実行します: test_number={test_number:?}");
                        self.test_service.run_test(&contest, test_number)
                    }
                )
            }
            Command::Submit => {
                context.contest.map_or_else(
                    || Err(anyhow::anyhow!("コンテストが選択されていません")),
                    |contest| {
                        println!("提出を行います");
                        self.contest_service.submit(&contest)
                    }
                )
            }
        }
    }

    #[must_use = "この関数は新しいCommandContextインスタンスを返します"]
    pub fn with_contest(&self, command: Command, contest: Contest) -> CommandContext {
        CommandContext::with_contest(command, contest)
    }

    #[must_use = "この関数は新しいCommandContextインスタンスを返します"]
    pub fn without_contest(&self, command: Command) -> CommandContext {
        CommandContext::new(command)
    }
} 