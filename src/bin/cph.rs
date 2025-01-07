use std::env;
use anyhow::{Result, Context};
use cph::config::Config;
use cph::contest::parse::CommandParser;
use cph::contest::service::{CommandService, ContestService, TestService};

fn main() -> Result<()> {
    // コマンドライン引数を取得
    let args: Vec<String> = env::args().skip(1).collect();
    let input = args.join(" ");

    // 設定ファイルを読み込む
    let config = Config::load_from_file("src/config/config.yaml")
        .context("src/config/config.yamlの読み込みに失敗しました")?;

    // サービスを初期化
    let contest_service = ContestService::new(&config)?;
    let test_service = TestService::new(&config)?;
    let command_service = CommandService::new(contest_service, test_service);

    // コマンドをパースして実行
    let parser = CommandParser::new(&config)?;
    let context = parser.parse(&input)?;
    command_service.execute(context)?;

    Ok(())
}
