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
        self.save_config()?;

        // ワークスペースディレクトリを作成
        let workspace_dir = self.get_workspace_dir().join(contest_id);
        fs::create_dir_all(&workspace_dir)?;

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

        let workspace_dir = self.get_workspace_dir().join(&config.contest);
        
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
        let workspace_dir = self.get_workspace_dir();
        if !workspace_dir.exists() {
            return Ok(false);
        }

        if let Some(config) = &self.config {
            let contest_workspace = workspace_dir.join(&config.contest);
            if contest_workspace.exists() {
                let contests_dir = self.get_contests_dir();
                fs::create_dir_all(&contests_dir)?;

                let contest_archive = contests_dir.join(&config.contest);
                if contest_archive.exists() {
                    fs::remove_dir_all(&contest_archive)?;
                }
                fs::rename(&contest_workspace, &contest_archive)?;
            }
        }

        // 新しいワークスペースディレクトリを作成
        fs::create_dir_all(&workspace_dir)?;

        Ok(true)
    }
} 