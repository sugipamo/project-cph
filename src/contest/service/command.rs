use crate::contest::model::{Command, CommandContext, Contest};
use crate::contest::service::{ContestHandler, TestRunner};
use crate::config::Config;
use anyhow::Result;
use crate::message::contest;

pub struct Service {
    contest_service: ContestHandler,
    test_service: TestRunner,
    config: Config,
}

impl Service {
    /// `CommandService`の新しいインスタンスを作成します
    /// 
    /// # Errors
    /// 
    /// - 設定ファイルの読み込みに失敗した場合
    pub fn new(contest_service: ContestHandler, test_service: TestRunner) -> Result<Self> {
        let config = Config::load()?;
        Ok(Self {
            contest_service,
            test_service,
            config,
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
                    |site_str| {
                        // 設定からテンプレートディレクトリを取得
                        let template_dir = self.config.contest_template_dir();
                        let active_dir = self.config.active_contest_dir();
                        
                        self.contest_service.open_with_config(
                            &site_str,
                            &contest_id,
                            &problem_id,
                            &template_dir,
                            &active_dir,
                        )
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
                    |contest| {
                        println!("テストを実行します: test_number={test_number:?}");
                        // 設定からテストディレクトリを取得
                        let test_dir = self.config.test_dir();
                        let result = self.test_service.run_test_with_config(&contest, test_number, &test_dir)?;
                        println!("{}", result.summary());
                        Ok(())
                    }
                )
            }
            Command::Submit => {
                context.contest.map_or_else(
                    || Err(anyhow::anyhow!(contest::error("invalid_command", "コンテストが選択されていません"))),
                    |contest| {
                        println!("提出を行います");
                        self.contest_service.submit(&contest)
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