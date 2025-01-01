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

    fn display_languages(&self, config: &Config, current: Option<&str>) -> Result<()> {
        println!("\n利用可能な言語:");
        if let Ok(languages) = config.get::<Vec<String>>("languages.available") {
            for lang in languages {
                let display_name = config.get::<String>(&format!("{}.display_name", lang))
                    .unwrap_or_else(|_| lang.clone());
                if let Ok(default_lang) = config.get::<String>("languages.default") {
                    if lang == default_lang {
                        if Some(lang.as_str()) == current {
                            println!("  * {} (デフォルト) - 現在の設定", display_name);
                        } else {
                            println!("  * {} (デフォルト)", display_name);
                        }
                        continue;
                    }
                }
                if Some(lang.as_str()) == current {
                    println!("  * {} - 現在の設定", display_name);
                } else {
                    println!("  * {}", display_name);
                }
            }
        }
        Ok(())
    }
}

#[async_trait::async_trait]
impl Command for LanguageCommand {
    async fn execute(&self, command: &Commands) -> Result<()> {
        println!("設定を読み込んでいます...");
        let config = Config::load()
            .map_err(|e| format!("設定の読み込みに失敗しました: {}", e))?;

        // コンテストを読み込む
        println!("コンテストの設定を読み込んでいます...");
        let mut contest = Contest::new(&config, &self.context.problem_id)?;

        match command {
            Commands::Language { language } => {
                println!("言語を検証しています: {}", language);
                // 言語を解析
                let resolved = match config.get_with_alias::<String>(&format!("{}.name", language)) {
                    Ok(lang) => lang,
                    Err(_) => {
                        println!("無効な言語が指定されました: {}", language);
                        self.display_languages(&config, contest.language.as_deref())?;
                        return Err(format!("無効な言語です: {}", language).into());
                    }
                };

                // 言語を設定
                if let Err(e) = contest.set_language(&resolved) {
                    println!("言語の設定に失敗しました: {}", e);
                    return Err(e.into());
                }

                // 設定を保存
                if let Err(e) = contest.save() {
                    println!("設定の保存に失敗しました: {}", e);
                    return Err(e.into());
                }

                println!("言語を設定しました: {}", resolved);
                Ok(())
            }
            _ => {
                // 現在の設定を表示
                if let Some(current) = &contest.language {
                    let display_name = config.get::<String>(&format!("{}.display_name", current))
                        .unwrap_or_else(|_| current.to_string());
                    println!("現在の言語: {}", display_name);
                } else {
                    println!("言語が設定されていません");
                }

                // 利用可能な言語を表示
                self.display_languages(&config, contest.language.as_deref())?;
                Ok(())
            }
        }
    }
} 