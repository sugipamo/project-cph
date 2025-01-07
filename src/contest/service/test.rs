use anyhow::Result;
use crate::config::Config;
use crate::contest::model::Contest;

pub struct TestService {
    #[allow(dead_code)]
    config: Config,
}

impl TestService {
    pub fn new(config: &Config) -> Result<Self> {
        Ok(Self {
            config: config.clone(),
        })
    }

    pub fn run_test(&self, _contest: &Contest, test_number: Option<usize>) -> Result<()> {
        // TODO: 実際のテスト実行処理を実装
        match test_number {
            Some(n) => println!("テストケース {} を実行します", n),
            None => println!("全てのテストケースを実行します"),
        }
        Ok(())
    }
} 