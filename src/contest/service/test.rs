use anyhow::Result;
use crate::config::Config;
use crate::contest::model::Contest;

pub struct Service {
    #[allow(dead_code)]
    config: Config,
}

impl Service {
    /// 新しいテスターを作成します。
    /// 
    /// # Errors
    /// - 設定の読み込みに失敗した場合
    #[must_use = "この関数は新しいTestServiceインスタンスを返します"]
    pub fn new(config: &Config) -> Result<Self> {
        Ok(Self {
            config: config.clone(),
        })
    }

    /// テストを実行します。
    /// 
    /// # Errors
    /// - テストの実行に失敗した場合
    pub fn run_test(&self, _contest: &Contest, test_number: Option<usize>) -> Result<()> {
        // TODO: 実際のテスト実行処理を実装
        match test_number {
            Some(n) => println!("テストケース {n} を実行します"),
            None => println!("全てのテストケースを実行します"),
        }
        Ok(())
    }
} 