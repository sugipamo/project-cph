use super::{Command, Result, CommandContext};
use crate::cli::Commands;
use crate::workspace::Workspace;
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

impl Command for LanguageCommand {
    fn execute(&self, command: &Commands) -> Result<()> {
        // ワークスペースを読み込む
        let mut workspace = Workspace::new(self.context.workspace_path.clone())?;

        match command {
            Commands::Language { language } => {
                // 言語を解析
                let language = Language::from_str(language)
                    .map_err(|e| format!("無効な言語です: {}", e))?;
                
                // 言語を設定
                workspace.set_language(language);
                workspace.save()?;

                println!("言語を設定しました: {:?}", language);
            }
            _ => {
                // 現在の設定を表示
                println!("現在の言語: {:?}", workspace.language);
            }
        }

        Ok(())
    }
} 