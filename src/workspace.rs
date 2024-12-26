use std::path::{Path, PathBuf};
use std::fs;
use glob::Pattern;
use crate::error::Result;
use crate::Language;

pub struct Workspace {
    root: PathBuf,
}

impl Workspace {
    pub fn new() -> Result<Self> {
        let root = std::env::current_dir()?;
        Ok(Self { root })
    }

    pub fn get_workspace_dir(&self) -> PathBuf {
        self.root.join("workspace")
    }

    pub fn get_template_dir(&self, language: Language) -> PathBuf {
        self.get_workspace_dir().join("template").join(language.to_string())
    }

    pub fn get_archive_dir(&self, contest_id: &str) -> PathBuf {
        self.root.join("archive").join(contest_id)
    }

    fn read_ignore_patterns(&self) -> Result<Vec<Pattern>> {
        let ignore_file = self.get_workspace_dir().join(".archiveignore");
        if !ignore_file.exists() {
            return Ok(Vec::new());
        }

        let content = fs::read_to_string(ignore_file)?;
        let patterns = content
            .lines()
            .filter(|line| !line.trim().is_empty() && !line.starts_with('#'))
            .map(|line| Pattern::new(line.trim()))
            .collect::<std::result::Result<Vec<_>, _>>()?;
        Ok(patterns)
    }

    pub fn archive_current_workspace(&self, new_contest_id: &str) -> Result<()> {
        let workspace_dir = self.get_workspace_dir();
        let archive_dir = self.get_archive_dir(new_contest_id);
        let ignore_patterns = self.read_ignore_patterns()?;

        // アーカイブディレクトリを作成
        fs::create_dir_all(&archive_dir)?;

        // ワークスペース内のファイルをスキャン
        for entry in fs::read_dir(&workspace_dir)? {
            let entry = entry?;
            let path = entry.path();
            let relative_path = path.strip_prefix(&workspace_dir)?;
            let relative_path_str = relative_path.to_string_lossy();

            // 無視パターンに一致するかチェック
            if ignore_patterns.iter().any(|pattern| pattern.matches(&relative_path_str)) {
                continue;
            }

            // ファイルを移動
            if path.is_file() {
                let target = archive_dir.join(relative_path);
                if let Some(parent) = target.parent() {
                    fs::create_dir_all(parent)?;
                }
                fs::rename(&path, &target)?;
            }
        }

        Ok(())
    }

    pub fn setup_problem(&self, contest_id: &str, problem_id: &str, language: Language) -> Result<PathBuf> {
        // 現在のワークスペースをアーカイブ
        self.archive_current_workspace(contest_id)?;

        let workspace_dir = self.get_workspace_dir();
        fs::create_dir_all(&workspace_dir)?;

        // ソースファイルのパス
        let source_file = workspace_dir.join(format!("{}.{}", problem_id, language.extension()));

        // テンプレートの選択とコピー
        let template_dir = self.get_template_dir(language);
        if template_dir.exists() {
            let template_file = template_dir.join(format!("main.{}", language.extension()));
            if template_file.exists() {
                fs::copy(template_file, &source_file)?;
            } else {
                fs::write(&source_file, language.default_content()?)?;
            }
        } else {
            fs::write(&source_file, language.default_content()?)?;
        }

        // contests.yamlの更新
        self.update_contest_info(contest_id, problem_id, &source_file)?;

        Ok(source_file)
    }

    fn update_contest_info(&self, contest_id: &str, problem_id: &str, source_file: &Path) -> Result<()> {
        use serde_yaml::{Mapping, Value};
        
        let workspace_dir = self.get_workspace_dir();
        let contests_file = workspace_dir.join("contests.yaml");
        
        // 既存のcontests.yamlを読み込むか、新規作成
        let mut contests: Mapping = if contests_file.exists() {
            serde_yaml::from_str(&fs::read_to_string(&contests_file)?)?
        } else {
            Mapping::new()
        };

        // コンテスト情報を更新
        let contest = contests
            .entry(Value::String(contest_id.to_string()))
            .or_insert(Value::Mapping(Mapping::new()));

        if let Value::Mapping(contest_map) = contest {
            let problems = contest_map
                .entry(Value::String("problems".to_string()))
                .or_insert(Value::Mapping(Mapping::new()));

            if let Value::Mapping(problems_map) = problems {
                let problem = problems_map
                    .entry(Value::String(problem_id.to_string()))
                    .or_insert(Value::Mapping(Mapping::new()));

                if let Value::Mapping(problem_map) = problem {
                    problem_map.insert(
                        Value::String("solution".to_string()),
                        Value::String(source_file.file_name().unwrap().to_string_lossy().to_string()),
                    );
                }
            }
        }

        // ファイルに書き戻す
        fs::write(&contests_file, serde_yaml::to_string(&contests)?)?;
        Ok(())
    }

    pub fn get_problem_url(&self, contest_id: &str, problem_id: &str) -> String {
        format!(
            "https://atcoder.jp/contests/{}/tasks/{}_{}", 
            contest_id, 
            contest_id, 
            problem_id
        )
    }
} 