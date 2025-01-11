use crate::contest::model::{Command, CommandContext, Contest};
use crate::contest::service::{ContestHandler, TestRunner};
use anyhow::Result;
use crate::message::contest;
use crate::config::Config;

#[derive(Default)]
pub struct Service {
    contest_service: ContestHandler,
    test_service: TestRunner,
}

impl Service {
    /// 新しいサービスインスタンスを作成します
    ///
    /// # Arguments
    ///
    /// * `contest_service` - コンテストサービス
    /// * `test_service` - テストサービス
    ///
    /// # Errors
    /// 
    /// - 設定ファイルの読み込みに失敗した場合
    pub fn new(contest_service: ContestHandler, test_service: TestRunner) -> Result<Self> {
        Ok(Self {
            contest_service,
            test_service,
        })
    }

    /// コマンドを実行します
    ///
    /// # Arguments
    ///
    /// * `command` - 実行するコマンド
    /// * `context` - コマンド実行コンテキスト
    ///
    /// # Errors
    ///
    /// - コマンドの実行に失敗した場合
    pub fn execute(&self, command: Command, context: CommandContext) -> Result<()> {
        match command {
            Command::Open { site, contest_id, problem_id } => {
                println!("問題を開きます: site={site:?}, contest={contest_id:?}, problem={problem_id:?}");
                site.map_or_else(
                    || Err(anyhow::anyhow!(contest::error("invalid_command", "サイトが指定されていません"))),
                    |site_str| {
                        // 設定からテンプレートディレクトリを取得
                        let template_dir = Config::get_default("contest.template_dir")?;
                        let active_dir = Config::get_default("contest.active_dir")?;
                        
                        self.contest_service.open_with_config(
                            &site_str,
                            contest_id.as_ref().ok_or_else(|| anyhow::anyhow!(contest::error("invalid_command", "コンテストIDが指定されていません")))?,
                            problem_id.as_ref().ok_or_else(|| anyhow::anyhow!(contest::error("invalid_command", "問題IDが指定されていません")))?,
                            &template_dir,
                            &active_dir,
                        )
                    }
                )
            }
            Command::List => {
                println!("問題一覧を表示します");
                Ok(())
            }
            Command::Test { test_number } => {
                context.contest.map_or_else(
                    || Err(anyhow::anyhow!(contest::error("invalid_command", "コンテストが選択されていません"))),
                    |contest| {
                        println!("テストを実行します: test_number={test_number:?}");
                        // 設定からテストディレクトリを取得
                        let test_dir: String = Config::get_default("contest.test_dir")?;
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
} 