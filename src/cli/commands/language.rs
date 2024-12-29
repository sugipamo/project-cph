use super::{Command, Result, CommandContext};
use crate::cli::Commands;
use crate::contest::Contest;
use std::str::FromStr;
use crate::Language;

pub struct LanguageCommand {
    context: CommandContext,
}

impl LanguageCommand {
    pub fn new(context: CommandContext) -> Self {
        Self { context }
    }
}

#[async_trait::async_trait]
impl Command for LanguageCommand {
    async fn execute(&self, command: &Commands) -> Result<()> {
        // コンテストを読み込む
        let mut contest = match Contest::new(self.context.active_contest_dir.clone()) {
            Ok(contest) => contest,
            Err(e) => {
                println!("コンテストの読み込みに失敗しました: {}", e);
                return Err(e.into());
            }
        };

        match command {
            Commands::Language { language } => {
                // 言語を解析
                let language = match Language::from_str(language) {
                    Ok(lang) => lang,
                    Err(e) => {
                        println!("無効な言語が指定されました: {}", e);
                        return Err(format!("無効な言語です: {}", e).into());
                    }
                };
                
                // 言語を設定
                contest.set_language(language);
                if let Err(e) = contest.save() {
                    println!("言語設定の保存に失敗しました: {}", e);
                    return Err(e.into());
                }

                println!("言語を設定しました: {:?}", language);
            }
            _ => {
                // 現在の設定を表示
                println!("現在の言語: {:?}", contest.language);
            }
        }

        Ok(())
    }
} 