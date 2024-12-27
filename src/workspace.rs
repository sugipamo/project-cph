use std::fs;
use std::path::{Path, PathBuf};
use serde::{Deserialize, Serialize};
use crate::error::{Result, Error};
use crate::{Language, cli::Site};

#[derive(Debug, Serialize, Deserialize)]
pub struct Config {
    pub contest: String,
    pub language: Language,
    pub site: Site,
}

pub struct Workspace {
    root: PathBuf,
    config: Option<Config>,
}

impl Workspace {
    pub fn new(root: PathBuf) -> Self {
        let config = Self::load_config(&root).ok();
        Self { root, config }
    }

    fn load_config(root: &Path) -> Result<Config> {
        let config_path = root.join("workspace").join("contests.yaml");
        if config_path.exists() {
            let contents = std::fs::read_to_string(&config_path)?;
            Ok(serde_yaml::from_str(&contents)?)
        } else {
            Err(Error::InvalidInput("No active contest. Use 'workspace' command to set one.".to_string()))
        }
    }

    fn save_config(&self) -> Result<()> {
        let workspace_dir = self.get_workspace_dir();
        fs::create_dir_all(&workspace_dir)?;
        let config_path = workspace_dir.join("contests.yaml");
        if let Some(config) = &self.config {
            let contents = serde_yaml::to_string(&config)?;
            std::fs::write(config_path, contents)?;
        }
        Ok(())
    }

    pub fn set_workspace(&mut self, contest_id: &str, site: Site) -> Result<()> {
        // 現在のワークスペースをアーカイブ
        self.archive_current_workspace()?;

        // 新しいワークスペースを設定
        let language = self.config.as_ref().map(|c| c.language).unwrap_or(Language::Rust);
        self.config = Some(Config {
            contest: contest_id.to_string(),
            language,
            site,
        });

        // ワークスペースディレクトリを作成
        let workspace_dir = self.get_workspace_dir();
        fs::create_dir_all(&workspace_dir)?;
        self.save_config()?;

        // テンプレートファイルをコピー
        self.copy_template_files()?;

        Ok(())
    }

    fn copy_template_files(&self) -> Result<()> {
        let template_dir = self.root.join("src").join("templates");
        let workspace_dir = self.get_workspace_dir();

        // .moveignoreをコピー
        if !workspace_dir.join(".moveignore").exists() {
            fs::copy(
                template_dir.join(".moveignore"),
                workspace_dir.join(".moveignore"),
            )?;
        }

        Ok(())
    }

    pub fn set_language(&mut self, language: Language) -> Result<()> {
        if let Some(config) = &mut self.config {
            config.language = language;
            self.save_config()?;
            Ok(())
        } else {
            Err(Error::InvalidInput("No active contest. Use 'workspace' command to set one.".to_string()))
        }
    }

    pub fn setup_problem(&mut self, problem_id: &str) -> Result<PathBuf> {
        let config = self.config.as_ref()
            .ok_or_else(|| Error::InvalidInput("No active contest. Use 'workspace' command to set one.".to_string()))?;

        let workspace_dir = self.get_workspace_dir();
        fs::create_dir_all(&workspace_dir)?;
        
        // ソースファイルを作成
        let source_path = workspace_dir.join(format!("{}.{}", problem_id, config.language.extension()));
        if !source_path.exists() {
            fs::write(&source_path, config.language.default_content()?)?;
        }

        Ok(source_path)
    }

    pub fn get_current_config(&self) -> Option<&Config> {
        self.config.as_ref()
    }

    pub fn get_workspace_dir(&self) -> PathBuf {
        self.root.join("workspace")
    }

    pub fn get_contests_dir(&self) -> PathBuf {
        self.root.join("contests")
    }

    pub fn archive_current_workspace(&self) -> Result<bool> {
        if let Some(config) = &self.config {
            let workspace_dir = self.get_workspace_dir();
            if workspace_dir.exists() {
                // .moveignoreの内容を読み込む
                let ignore_patterns = if let Ok(contents) = fs::read_to_string(workspace_dir.join(".moveignore")) {
                    contents.lines()
                        .filter(|line| !line.trim().is_empty() && !line.starts_with('#'))
                        .map(|s| s.to_string())
                        .collect::<Vec<_>>()
                } else {
                    Vec::new()
                };

                // contests/abc***ディレクトリを作成
                let contests_dir = self.get_contests_dir();
                let contest_archive = contests_dir.join(&config.contest);
                fs::create_dir_all(&contest_archive)?;

                // ワークスペース内のファイルを移動（.moveignoreに含まれていないもののみ）
                for entry in fs::read_dir(&workspace_dir)? {
                    let entry = entry?;
                    let path = entry.path();
                    if let Some(file_name) = path.file_name().and_then(|n| n.to_str()) {
                        if file_name == "contests.yaml" || file_name == ".moveignore" {
                            continue;
                        }

                        // .moveignoreのパターンに一致するかチェック
                        let should_ignore = ignore_patterns.iter()
                            .any(|pattern| file_name.starts_with(pattern.as_str()));

                        if !should_ignore {
                            let target_path = contest_archive.join(file_name);
                            fs::rename(&path, &target_path)?;
                        }
                    }
                }

                // workspaceディレクトリを削除して再作成
                fs::remove_dir_all(&workspace_dir)?;
                fs::create_dir_all(&workspace_dir)?;
            }
        }

        Ok(true)
    }
} 