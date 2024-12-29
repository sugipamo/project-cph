use std::fs;
use std::path::PathBuf;
use clap::ArgMatches;
use serde::{Deserialize, Serialize};
use super::{Command, CommandContext, Result};

/// 言語設定コマンド
pub struct LanguageCommand {
    context: CommandContext,
}

#[derive(Debug, Serialize, Deserialize)]
struct ContestConfig {
    #[serde(default)]
    language: Option<String>,
}

impl LanguageCommand {
    pub fn new(context: CommandContext) -> Self {
        Self { context }
    }

    /// 設定ファイルを読み込む
    fn load_config(&self, config_path: &PathBuf) -> Result<ContestConfig> {
        if config_path.exists() {
            let content = fs::read_to_string(config_path)?;
            Ok(serde_yaml::from_str(&content)
                .map_err(|e| format!("設定ファイルの解析に失敗しました: {}", e))?)
        } else {
            Ok(ContestConfig { language: None })
        }
    }

    /// 設定ファイルを保存する
    fn save_config(&self, config_path: &PathBuf, config: &ContestConfig) -> Result<()> {
        let content = serde_yaml::to_string(config)
            .map_err(|e| format!("設定ファイルの生成に失敗しました: {}", e))?;
        fs::write(config_path, content)?;
        Ok(())
    }

    /// 現在のディレクトリからcontests.yamlを探す
    fn find_config_file(&self) -> Option<PathBuf> {
        let mut current_dir = self.context.workspace_path.clone();
        while current_dir.parent().is_some() {
            let config_path = current_dir.join("contests.yaml");
            if config_path.exists() {
                return Some(config_path);
            }
            current_dir = current_dir.parent().unwrap().to_path_buf();
        }
        None
    }
}

impl Command for LanguageCommand {
    fn execute(&self, matches: &ArgMatches) -> Result<()> {
        let config_path = self.find_config_file()
            .ok_or("contests.yamlが見つかりません。workコマンドでワークスペースを作成してください。")?;

        // 設定を読み込む
        let mut config = self.load_config(&config_path)?;

        if let Some(language) = matches.get_one::<String>("language") {
            // 言語を設定
            config.language = Some(language.clone());
            self.save_config(&config_path, &config)?;
            println!("言語を設定しました: {}", language);
        } else {
            // 現在の設定を表示
            match config.language {
                Some(lang) => println!("現在の言語: {}", lang),
                None => println!("言語が設定されていません"),
            }
        }

        Ok(())
    }
} 