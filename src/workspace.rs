use std::fs;
use std::path::{Path, PathBuf};
use glob::glob;
use serde::{Deserialize, Serialize};
use crate::error::Result;
use crate::Language;

#[derive(Debug, Serialize, Deserialize)]
struct Problem {
    solution: String,
}

#[derive(Debug, Serialize, Deserialize)]
struct Contest {
    problems: std::collections::HashMap<String, Problem>,
}

#[derive(Debug, Serialize, Deserialize)]
struct Config {
    contests: std::collections::HashMap<String, Contest>,
}

pub struct Workspace {
    root_dir: PathBuf,
}

impl Workspace {
    pub fn new(root_dir: PathBuf) -> Self {
        Self { root_dir }
    }

    pub fn get_workspace_dir(&self) -> PathBuf {
        self.root_dir.join("workspace")
    }

    pub fn get_archive_dir(&self) -> PathBuf {
        self.root_dir.join("archive")
    }

    pub fn archive_current_workspace(&self) -> Result<()> {
        let workspace_dir = self.get_workspace_dir();

        // contests.yamlを読み込む
        let config_path = workspace_dir.join("contests.yaml");
        if !config_path.exists() {
            return Ok(());  // contests.yamlが存在しない場合は何もしない
        }

        let config_str = fs::read_to_string(&config_path)?;
        let config: Config = serde_yaml::from_str(&config_str)?;

        // アーカイブ対象のコンテストを特定
        let contest_id = config.contests.keys().next().ok_or_else(|| {
            crate::error::Error::InvalidInput("No contest found in contests.yaml".to_string())
        })?;

        // アーカイブディレクトリを作成
        let archive_dir = self.get_archive_dir().join(contest_id);
        fs::create_dir_all(&archive_dir)?;

        // .archiveignoreの内容を読み込む
        let ignore_patterns = self.read_ignore_patterns()?;

        // ワークスペース内のファイルをアーカイブ
        for entry in fs::read_dir(&workspace_dir)? {
            let entry = entry?;
            let path = entry.path();

            // .archiveignoreに含まれるファイルはスキップ
            if self.should_ignore(&path, &ignore_patterns)? {
                continue;
            }

            // ファイルをアーカイブディレクトリにコピー
            if path.is_file() {
                let file_name = path.file_name().unwrap();
                fs::copy(&path, archive_dir.join(file_name))?;
                fs::remove_file(&path)?;
            }
        }

        Ok(())
    }

    fn read_ignore_patterns(&self) -> Result<Vec<String>> {
        let ignore_file = self.get_workspace_dir().join(".archiveignore");
        if !ignore_file.exists() {
            return Ok(Vec::new());
        }

        let content = fs::read_to_string(ignore_file)?;
        Ok(content.lines()
            .filter(|line| !line.trim().is_empty() && !line.starts_with('#'))
            .map(|line| line.trim().to_string())
            .collect())
    }

    fn should_ignore(&self, path: &Path, patterns: &[String]) -> Result<bool> {
        let workspace_dir = self.get_workspace_dir();
        path.strip_prefix(&workspace_dir)?;

        for pattern in patterns {
            for matched in glob(&format!("{}/{}", workspace_dir.to_str().unwrap(), pattern))? {
                if let Ok(matched) = matched {
                    if matched == path {
                        return Ok(true);
                    }
                }
            }
        }

        Ok(false)
    }

    pub fn setup_problem(&self, contest_id: &str, problem_id: &str, language: Language) -> Result<PathBuf> {
        // 現在のワークスペースをアーカイブ
        self.archive_current_workspace()?;

        let workspace_dir = self.get_workspace_dir();

        // ソースファイルを作成
        let source_path = workspace_dir.join(format!("{}.{}", problem_id, language.extension()));
        fs::write(&source_path, language.default_content()?)?;

        // contests.yamlを更新
        let config_path = workspace_dir.join("contests.yaml");
        let mut config = if config_path.exists() {
            let config_str = fs::read_to_string(&config_path)?;
            serde_yaml::from_str(&config_str)?
        } else {
            Config {
                contests: std::collections::HashMap::new(),
            }
        };

        let contest = config.contests.entry(contest_id.to_string()).or_insert_with(|| Contest {
            problems: std::collections::HashMap::new(),
        });

        contest.problems.insert(problem_id.to_string(), Problem {
            solution: format!("{}.{}", problem_id, language.extension()),
        });

        let yaml = serde_yaml::to_string(&config)?;
        fs::write(config_path, yaml)?;

        Ok(source_path)
    }
} 