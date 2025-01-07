use crate::contest::model::{Command, CommandContext, Contest};
use crate::contest::service::{ContestService, TestService};
use anyhow::Result;

pub struct CommandService {
    contest_service: ContestService,
    test_service: TestService,
}

impl CommandService {
    pub fn new(contest_service: ContestService, test_service: TestService) -> Self {
        Self {
            contest_service,
            test_service,
        }
    }

    pub fn execute(&self, context: CommandContext) -> Result<()> {
        match context.command {
            Command::Login => {
                // TODO: ログイン処理の実装
                println!("ログイン処理を実行します");
                Ok(())
            }
            Command::Open { site, contest_id, problem_id } => {
                println!("問題を開きます: site={}, contest={:?}, problem={:?}", 
                    site, contest_id, problem_id);
                self.contest_service.open(site, contest_id, problem_id)
            }
            Command::Test { test_number } => {
                if let Some(contest) = context.contest {
                    println!("テストを実行します: test_number={:?}", test_number);
                    self.test_service.run_test(&contest, test_number)
                } else {
                    Err(anyhow::anyhow!("コンテストが選択されていません"))
                }
            }
            Command::Submit => {
                if let Some(contest) = context.contest {
                    println!("提出を行います");
                    self.contest_service.submit(&contest)
                } else {
                    Err(anyhow::anyhow!("コンテストが選択されていません"))
                }
            }
        }
    }

    pub fn with_contest(&self, command: Command, contest: Contest) -> CommandContext {
        CommandContext::with_contest(command, contest)
    }

    pub fn without_contest(&self, command: Command) -> CommandContext {
        CommandContext::new(command)
    }
} 