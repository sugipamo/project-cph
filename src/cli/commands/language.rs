use super::{Command, Result, CommandContext};
use crate::cli::Commands;
use crate::error::Result;
use crate::contest::Contest;

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
        println!("言語設定を読み込んでいます...");
        let config_paths = config::get_config_paths();
        let lang_config = match LanguageConfig::load(config_paths.languages) {
            Ok(config) => config,
            Err(e) => {
                println!("言語設定の読み込みに失敗しました: {}", e);
                return Err(e.into());
            }
        };

        // コンテストを読み込む
        println!("コンテストの設定を読み込んでいます...");
        let mut contest = match Contest::new(self.context.active_contest_dir.clone()) {
            Ok(contest) => contest,
            Err(e) => {
                println!("コンテストの読み込みに失敗しました: {}", e);
                return Err(e.into());
            }
        };

        match command {
            Commands::Language { language } => {
                println!("言語を検証しています: {}", language);
                // 言語を解析
                let resolved = match lang_config.resolve_language(language) {
                    Some(lang) => lang,
                    None => {
                        println!("無効な言語が指定されました: {}", language);
                        println!("利用可能な言語:");
                        for lang in lang_config.list_languages() {
                            let display_name = lang_config.get_display_name(&lang)
                                .unwrap_or_else(|| lang.clone());
                            if Some(lang.clone()) == lang_config.get_default_language() {
                                println!("  * {} (デフォルト)", display_name);
                            } else {
                                println!("  * {}", display_name);
                            }
                        }
                        return Err(format!("無効な言語です: {}", language).into());
                    }
                };
                
                // 言語を設定
                println!("言語を設定しています...");
                contest.set_language(&resolved);
                if let Err(e) = contest.save() {
                    println!("言語設定の保存に失敗しました: {}", e);
                    return Err(e.into());
                }

                println!("言語を設定しました: {}", 
                    lang_config.get_display_name(&resolved)
                        .unwrap_or(resolved));
            }
            _ => {
                // 現在の設定を表示
                if let Some(current) = &contest.language {
                    let display_name = lang_config.get_display_name(current)
                        .unwrap_or_else(|| current.to_string());
                    if Some(current.clone()) == lang_config.get_default_language() {
                        println!("現在の言語: {} (デフォルト)", display_name);
                    } else {
                        println!("現在の言語: {}", display_name);
                    }
                } else {
                    println!("言語が設定されていません");
                }
                
                println!("\n利用可能な言語:");
                for lang in lang_config.list_languages() {
                    let display_name = lang_config.get_display_name(&lang)
                        .unwrap_or_else(|| lang.clone());
                    if Some(lang.clone()) == lang_config.get_default_language() {
                        println!("  * {} (デフォルト)", display_name);
                    } else {
                        println!("  * {}", display_name);
                    }
                }
            }
        }

        Ok(())
    }
} 