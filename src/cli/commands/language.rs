use super::{Command, Result, CommandContext};
use crate::cli::Commands;
use crate::contest::Contest;
use crate::config::Config;

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
        println!("設定を読み込んでいます...");
        let config = Config::builder()
            .map_err(|e| format!("設定の読み込みに失敗しました: {}", e))?;

        // コンテストを読み込む
        println!("コンテストの設定を読み込んでいます...");
        let mut contest = Contest::new(self.context.active_contest_dir.clone())?;

        match command {
            Commands::Language { language } => {
                println!("言語を検証しています: {}", language);
                // 言語を解析
                let resolved = match config.get_with_alias::<String>(&format!("{}.name", language)) {
                    Ok(lang) => lang,
                    Err(_) => {
                        println!("無効な言語が指定されました: {}", language);
                        println!("利用可能な言語:");
                        if let Ok(languages) = config.get::<Vec<String>>("languages.available") {
                            for lang in languages {
                                let display_name = config.get::<String>(&format!("{}.display_name", lang))
                                    .unwrap_or_else(|_| lang.clone());
                                if let Ok(default_lang) = config.get::<String>("languages.default") {
                                    if lang == default_lang {
                                        println!("  * {} (デフォルト)", display_name);
                                        continue;
                                    }
                                }
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

                let display_name = config.get::<String>(&format!("{}.display_name", resolved))
                    .unwrap_or_else(|_| resolved.to_string());
                println!("言語を設定しました: {}", display_name);
            }
            _ => {
                // 現在の設定を表示
                if let Some(current) = &contest.language {
                    let display_name = config.get::<String>(&format!("{}.display_name", current))
                        .unwrap_or_else(|_| current.to_string());
                    if let Ok(default_lang) = config.get::<String>("languages.default") {
                        if current == &default_lang {
                            println!("現在の言語: {} (デフォルト)", display_name);
                        } else {
                            println!("現在の言語: {}", display_name);
                        }
                    } else {
                        println!("現在の言語: {}", display_name);
                    }
                } else {
                    println!("言語が設定されていません");
                }
                
                println!("\n利用可能な言語:");
                if let Ok(languages) = config.get::<Vec<String>>("languages.available") {
                    for lang in languages {
                        let display_name = config.get::<String>(&format!("{}.display_name", lang))
                            .unwrap_or_else(|_| lang.to_string());
                        if let Ok(default_lang) = config.get::<String>("languages.default") {
                            if lang == default_lang {
                                println!("  * {} (デフォルト)", display_name);
                                continue;
                            }
                        }
                        println!("  * {}", display_name);
                    }
                }
            }
        }

        Ok(())
    }
} 