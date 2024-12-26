use std::fs;
use std::path::{Path, PathBuf};
use serde::{Deserialize, Serialize};
use crate::error::Result;
use crate::{Language, cli::Site};
use std::collections::HashMap;

#[derive(Debug, Serialize, Deserialize)]
pub struct ContestConfig {
    pub language: Language,
    pub site: Site,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct Contests {
    pub contests: HashMap<String, ContestConfig>,
}

pub struct Workspace {
    root: PathBuf,
    contests: Contests,
}

impl Workspace {
    pub fn new(root: PathBuf) -> Self {
        let contests = Self::load_contests(&root).unwrap_or_else(|_| Contests {
            contests: HashMap::new(),
        });
        
        Self { root, contests }
    }

    fn load_contests(root: &Path) -> Result<Contests> {
        let config_path = root.join("contests.yaml");
        if config_path.exists() {
            let contents = std::fs::read_to_string(&config_path)?;
            Ok(serde_yaml::from_str(&contents)?)
        } else {
            Ok(Contests {
                contests: HashMap::new(),
            })
        }
    }

    fn save_contests(&self) -> Result<()> {
        let config_path = self.root.join("contests.yaml");
        let contents = serde_yaml::to_string(&self.contests)?;
        std::fs::write(config_path, contents)?;
        Ok(())
    }

    pub fn setup_problem(&mut self, contest_id: &str, problem_id: &str, language: Language, site: Site) -> Result<PathBuf> {
        // 現在のワークスペースをアーカイブ
        self.archive_current_workspace()?;

        // コンテスト情報を保存
        self.contests.contests.insert(contest_id.to_string(), ContestConfig {
            language,
            site,
        });
        self.save_contests()?;

        let workspace_dir = self.get_workspace_dir();
        let contest_dir = workspace_dir.join(contest_id);

        // コンテストディレクトリを作成
        fs::create_dir_all(&contest_dir)?;

        // ソースファイルを作成
        let source_path = contest_dir.join(format!("{}.{}", problem_id, language.extension()));
        fs::write(&source_path, language.default_content()?)?;

        Ok(source_path)
    }

    pub fn get_contest_config(&self, contest_id: &str) -> Option<&ContestConfig> {
        self.contests.contests.get(contest_id)
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

        // contests.yamlから現在のコンテストIDを取得
        let current_contests: Vec<_> = self.contests.contests.keys().cloned().collect();
        if current_contests.is_empty() {
            return Ok(false);
        }

        // コンテストディレクトリを移動
        let contests_dir = self.get_contests_dir();
        fs::create_dir_all(&contests_dir)?;

        for contest_id in current_contests {
            let contest_workspace = workspace_dir.join(&contest_id);
            if contest_workspace.exists() {
                let contest_archive = contests_dir.join(&contest_id);
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