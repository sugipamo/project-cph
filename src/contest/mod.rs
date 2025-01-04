use crate::config::Config;
use serde::{Serialize, Deserialize};
use std::path::{PathBuf, Path};
use std::fs;
use std::io::BufRead;

mod error;
mod parse;
mod file_manager;

use error::{Result, ContestError};
use file_manager::FileManager;

/// コンテスト情報を管理する構造体
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Contest {
    /// アクティブなコンテストのディレクトリ
    #[serde(default)]
    pub active_contest_dir: PathBuf,

    /// コンテスト情報
    pub contest: String,

    /// 問題ID
    pub problem: Option<String>,

    /// 使用言語
    pub language: Option<String>,

    /// サイトID（例: atcoder, codeforces）
    pub site: String,

    /// 設定情報
    #[serde(skip)]
    config: Config,

    /// ファイル操作マネージャー
    #[serde(skip)]
    file_manager: Option<FileManager>,
}

impl Contest {
    /// サイト認証用のコンテストインスタンスを作成
    pub fn for_site_auth(config: &Config) -> Result<Self> {
        Ok(Self {
            active_contest_dir: PathBuf::new(),
            contest: String::new(),
            problem: None,
            language: None,
            site: String::new(),
            config: config.clone(),
            file_manager: None,
        })
    }

    /// 新しいコンテストインスタンスを作成
    pub fn new(config: &Config, problem_id: &str) -> Result<Self> {
        let active_dir = config.get::<String>("system.contest_dir.active")
            .map_err(|e| ContestError::ConfigError(format!("アクティブディレクトリの設定取得に失敗: {}", e)))?;
        
        // 相対パスとして保持
        let active_contest_dir = PathBuf::from(&active_dir);

        let config_file = config.get::<String>("system.active_contest_yaml")
            .map_err(|e| ContestError::ConfigError(format!("コンテスト設定ファイル名の取得に失敗: {}", e)))?;
        let config_path = std::env::current_dir()
            .map_err(|e| ContestError::FileError { 
                source: e, 
                path: PathBuf::from(".") 
            })?
            .join(&active_dir)
            .join(&config_file);

        // FileManagerの初期化
        let mut file_manager = FileManager::new()?;

        // 既存の設定ファイルが存在する場合は読み込む
        let mut contest = if config_path.exists() {
            let content = fs::read_to_string(&config_path)
                .map_err(|e| ContestError::FileError { 
                    source: e, 
                    path: config_path.clone() 
                })?;
            let mut contest: Contest = serde_yaml::from_str(&content)
                .map_err(|e| ContestError::ConfigError(format!("{}の解析に失敗: {}", config_file, e)))?;
            
            contest.active_contest_dir = active_contest_dir;
            contest.problem = Some(problem_id.to_string());
            contest.config = config.clone();
            contest
        } else {
            // 新規作成時はデフォルト値で初期化
            let mut contest = Self {
                active_contest_dir,
                contest: String::new(),
                problem: Some(problem_id.to_string()),
                language: None,
                site: String::new(),
                config: config.clone(),
                file_manager: None,
            };

            // デフォルト言語を設定
            if let Ok(default_lang) = config.get::<String>("languages.default") {
                contest.language = Some(default_lang);
            }

            contest
        };

        contest.file_manager = Some(file_manager);
        Ok(contest)
    }

    /// login command: サイト認証を行う
    pub fn login(&self) -> Result<()> {
        // TODO: 実装
        Ok(())
    }

    /// open command: 問題ページを開く
    pub fn open(&self) -> Result<()> {
        // TODO: 実装
        Ok(())
    }

    /// test command: テストを実行
    pub fn run_test(&self, problem_id: &str) -> Result<()> {
        println!("TODO: Implement run_test for problem {}", problem_id);
        Ok(())
    }

    /// submit command: 解答を提出
    pub fn submit(&self) -> Result<()> {
        // TODO: 実装
        Ok(())
    }

    /// contest setting: コンテストIDを設定
    pub fn set_contest(&mut self, contest_id: String) {
        self.contest = contest_id;
    }

    /// language setting: 使用言語を設定
    pub fn set_language(&mut self, language: &str) -> Result<()> {
        let resolved_language = self.config.get_with_alias::<String>(&format!("{}.name", language))
            .unwrap_or_else(|_| language.to_string());

        self.config.get::<String>(&format!("languages.{}.extension", resolved_language))
            .map_err(|e| ContestError::ConfigError(
                format!("言語{}は存在しません: {}", resolved_language, e)
            ))?;
        self.language = Some(resolved_language);
        Ok(())
    }

    /// site setting: サイトを設定
    pub fn set_site(&mut self, site_id: &str) -> Result<()> {
        self.config.get::<String>(&format!("sites.{}.problem_url", site_id))
            .map_err(|e| ContestError::ConfigError(
                format!("サイト{}は存在しません: {}", site_id, e)
            ))?;
        self.site = site_id.to_string();
        Ok(())
    }

    /// サイトのURLを生成
    fn get_site_url(&self, url_type: &str, problem_id: &str) -> Result<String> {
        let pattern = self.config.get::<String>(&format!("sites.{}.{}_url", self.site, url_type))
            .map_err(|e| ContestError::ConfigError(
                format!("サイトURLパターンの取得に失敗: {}", e)
            ))?;
        
        let site_url = self.config.get::<String>(&format!("sites.{}.url", self.site))
            .map_err(|e| ContestError::ConfigError(
                format!("サイトURLの取得に失敗: {}", e)
            ))?;

        Ok(pattern
            .replace("{url}", &site_url)
            .replace("{contest}", &self.contest)
            .replace("{problem}", problem_id))
    }

    /// 問題のURLを取得
    pub fn get_problem_url(&self, problem_id: &str) -> Result<String> {
        self.get_site_url("problem", problem_id)
    }

    /// 提出のURLを取得
    pub fn get_submit_url(&self, problem_id: &str) -> Result<String> {
        self.get_site_url("submit", problem_id)
    }

    /// コンテストの設定を保存
    pub fn save(&self) -> Result<()> {
        let config_file = self.config.get::<String>("system.active_contest_yaml")
            .map_err(|e| ContestError::ConfigError(
                format!("コンテスト設定ファイル名の取得に失敗: {}", e)
            ))?;
        let config_path = self.active_contest_dir.join(&config_file);

        // FileManagerを使用してバックアップを作成
        if let Some(file_manager) = &self.file_manager {
            file_manager.backup(&self.active_contest_dir)?;
        }

        let content = serde_yaml::to_string(&self)
            .map_err(|e| ContestError::ConfigError(
                format!("コンテスト設定のシリアライズに失敗: {}", e)
            ))?;

        // 設定ファイルの保存を試みる
        if let Err(e) = fs::write(&config_path, &content) {
            // エラーが発生した場合、バックアップから復元
            if let Some(file_manager) = &self.file_manager {
                file_manager.rollback()?;
            }
            return Err(ContestError::FileError {
                source: e,
                path: config_path,
            });
        }

        // ファイルの移動を試みる
        if let Err(e) = self.move_files_to_contests() {
            // エラーが発生した場合、バックアップから復元
            if let Some(file_manager) = &self.file_manager {
                file_manager.rollback()?;
            }
            return Err(e);
        }

        // 成功した場合、バックアップをクリーンアップ
        if let Some(file_manager) = &self.file_manager {
            file_manager.cleanup()?;
        }

        Ok(())
    }

    /// テンプレートディレクトリのパスを取得
    fn get_template_dir(&self, language: &str) -> Result<PathBuf> {
        let template_pattern = self.config.get::<String>("system.templates.directory")
            .map_err(|e| ContestError::ConfigError(
                format!("テンプレートパターンの取得に失敗: {}", e)
            ))?;
        let template_base = self.config.get::<String>("system.contest_dir.template")
            .map_err(|e| ContestError::ConfigError(
                format!("テンプレートディレクトリの設定取得に失敗: {}", e)
            ))?;
        
        let template_dir_name = template_pattern.replace("{name}", language);
        Ok(self.get_absolute_contest_dir()?
            .parent()
            .unwrap()
            .join(template_base)
            .join(template_dir_name))
    }

    /// コンテスト保存用ディレクトリのパスを取得
    fn get_contests_dir(&self) -> Result<PathBuf> {
        let storage_base = self.config.get::<String>("system.contest_dir.storage")
            .map_err(|e| ContestError::ConfigError(
                format!("コンテスト保存先ディレクトリの設定取得に失敗: {}", e)
            ))?;
        Ok(self.get_absolute_contest_dir()?
            .parent()
            .unwrap()
            .join(storage_base))
    }

    /// 問題ファイルのパスを取得
    fn get_problem_file_path(&self, problem_id: &str, file_type: &str) -> Result<PathBuf> {
        let language = self.language.as_ref()
            .ok_or_else(|| ContestError::ValidationError(
                "言語が設定されていません".to_string()
            ))?;

        let extension = self.config.get::<String>(&format!("languages.{}.extension", language))
            .map_err(|e| ContestError::ConfigError(
                format!("言語{}の拡張子取得に失敗: {}", language, e)
            ))?;

        let pattern = self.config.get::<String>(&format!("system.templates.patterns.{}", file_type))
            .map_err(|e| ContestError::ConfigError(
                format!("ファイルパターンの取得に失敗: {}", e)
            ))?;

        let file_name = pattern.replace("{extension}", &extension);
        Ok(self.active_contest_dir.join(problem_id).join(file_name))
    }

    /// ソリューションファイルのパスを取得
    pub fn get_solution_path(&self, problem_id: &str) -> Result<PathBuf> {
        self.get_problem_file_path(problem_id, "solution")
    }

    /// ジェネレータファイルのパスを取得
    pub fn get_generator_path(&self, problem_id: &str) -> Result<PathBuf> {
        self.get_problem_file_path(problem_id, "generator")
    }

    /// テスターファイルのパスを取得
    pub fn get_tester_path(&self, problem_id: &str) -> Result<PathBuf> {
        self.get_problem_file_path(problem_id, "tester")
    }

    /// テストディレクトリのパスを取得
    pub fn get_test_dir(&self, problem_id: &str) -> Result<PathBuf> {
        let test_dir = self.config.get::<String>("system.test.dir")
            .map_err(|e| format!("テストディレクトリの設定取得に失敗: {}", e))?;
        Ok(self.get_absolute_contest_dir()?.join(problem_id).join(test_dir))
    }

    /// パス解決のためのヘルパーメソッド
    fn get_absolute_contest_dir(&self) -> Result<PathBuf> {
        std::env::current_dir()
            .map_err(|e| ContestError::FileError {
                source: e,
                path: PathBuf::from("."),
            })?
            .join(&self.active_contest_dir)
    }

    /// ディレクトリ内容を再帰的にコピー
    fn copy_dir_contents(&self, source: &Path, target: &Path) -> Result<()> {
        for entry in fs::read_dir(source)
            .map_err(|e| ContestError::FileError {
                source: e,
                path: source.to_path_buf(),
            })? {
            let entry = entry.map_err(|e| ContestError::FileError {
                source: e,
                path: source.to_path_buf(),
            })?;
            let file_type = entry.file_type()
                .map_err(|e| ContestError::FileError {
                    source: e,
                    path: entry.path(),
                })?;
            let source_path = entry.path();
            let file_name = entry.file_name();
            let target_path = target.join(&file_name);

            if file_type.is_dir() {
                if !target_path.exists() {
                    println!("ディレクトリを作成: {}", target_path.display());
                    fs::create_dir_all(&target_path)
                        .map_err(|e| ContestError::FileError {
                            source: e,
                            path: target_path.clone(),
                        })?;
                }
                self.copy_dir_contents(&source_path, &target_path)?;
            } else {
                if !target_path.exists() {
                    println!("ファイルをコピー: {} -> {}", source_path.display(), target_path.display());
                    fs::copy(&source_path, &target_path)
                        .map_err(|e| ContestError::FileError {
                            source: e,
                            path: target_path.clone(),
                        })?;
                } else {
                    println!("ファイルはすでに存在します（スキップ）: {}", target_path.display());
                }
            }
        }
        Ok(())
    }

    /// ファイルをcontestsディレクトリに移動
    fn move_files_to_contests(&self) -> Result<()> {
        let _ignore_patterns = self.read_moveignore()?;
        
        let contests_dir = self.get_contests_dir()?;

        // FileManagerを使用してバックアップを作成
        if let Some(file_manager) = &self.file_manager {
            file_manager.backup(&contests_dir)?;
        }

        // ディレクトリの作成を試みる
        if !contests_dir.exists() {
            if let Err(e) = fs::create_dir_all(&contests_dir) {
                // エラーが発生した場合、バックアップから復元
                if let Some(file_manager) = &self.file_manager {
                    file_manager.rollback()?;
                }
                return Err(ContestError::FileError {
                    source: e,
                    path: contests_dir,
                });
            }
        }

        let contest_dir = contests_dir.join(&self.contest);
        if !contest_dir.exists() {
            if let Err(e) = fs::create_dir_all(&contest_dir) {
                // エラーが発生した場合、バックアップから復元
                if let Some(file_manager) = &self.file_manager {
                    file_manager.rollback()?;
                }
                return Err(ContestError::FileError {
                    source: e,
                    path: contest_dir,
                });
            }
        }

        // 成功した場合、バックアップをクリーンアップ
        if let Some(file_manager) = &self.file_manager {
            file_manager.cleanup()?;
        }

        Ok(())
    }

    /// .moveignoreファイルを読み込む
    fn read_moveignore(&self) -> Result<Vec<String>> {
        let moveignore_path = self.active_contest_dir.join(".moveignore");
        let mut patterns = vec![];

        if !moveignore_path.exists() {
            let config_file = self.config.get::<String>("system.active_contest_yaml")
                .map_err(|e| format!("コンテスト設定ファイル名の取得に失敗: {}", e))?;

            let mut ignore_patterns = vec![config_file];
            if let Ok(additional_patterns) = self.config.get::<Vec<String>>("system.ignore_patterns") {
                ignore_patterns.extend(additional_patterns);
            }
            return Ok(ignore_patterns);
        }

        let file = fs::File::open(moveignore_path)
            .map_err(|e| format!(".moveignoreファイルの読み込みに失敗: {}", e))?;
        let reader = std::io::BufReader::new(file);

        for line in reader.lines() {
            let line = line.map_err(|e| format!(".moveignoreファイルの行の読み込みに失敗: {}", e))?;
            let line = line.trim();
            
            if !line.is_empty() && !line.starts_with('#') {
                patterns.push(line.to_string());
            }
        }

        Ok(patterns)
    }

    /// ファイルが.moveignoreパターンに一致するか確認
    #[allow(dead_code)]
    fn should_ignore(&self, file_name: &str, patterns: &[String]) -> bool {
        patterns.iter().any(|pattern| {
            if pattern.ends_with("/**") {
                let dir_pattern = &pattern[..pattern.len() - 3];
                file_name.starts_with(dir_pattern)
            } else {
                file_name == pattern
            }
        })
    }

    /// 問題ディレクトリを作成し、テンプレートをコピー
    pub fn create_problem_directory(&self, problem_id: &str) -> Result<()> {
        let language = self.language.as_ref()
            .ok_or_else(|| ContestError::ValidationError(
                "言語が設定されていません".to_string()
            ))?;

        let template_dir = self.get_template_dir(language)?;
        let problem_dir = self.active_contest_dir.join(problem_id);

        if !problem_dir.exists() {
            fs::create_dir_all(&problem_dir)
                .map_err(|e| ContestError::FileError {
                    source: e,
                    path: problem_dir.clone(),
                })?;
        }

        let test_dir = self.get_test_dir(problem_id)?;
        if !test_dir.exists() {
            fs::create_dir_all(&test_dir)
                .map_err(|e| ContestError::FileError {
                    source: e,
                    path: test_dir.clone(),
                })?;
        }

        if !template_dir.exists() {
            return Err(ContestError::ValidationError(
                format!("テンプレートディレクトリが見つかりません: {}", template_dir.display())
            ));
        }

        println!("テンプレートをコピーしています...");
        println!("From: {}", template_dir.display());
        println!("To: {}", problem_dir.display());

        self.copy_dir_contents(&template_dir, &problem_dir)?;

        println!("テンプレートのコピーが完了しました");
        Ok(())
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use tempfile::tempdir;

    fn create_test_config() -> Config {
        let config = r#"
system:
  contest_dir:
    active: "active"
    storage: "contests"
    template: "templates"
  active_contest_yaml: "contest.yaml"
  templates:
    directory: "{name}"
    patterns:
      solution: "main.{extension}"
      generator: "gen.{extension}"
      tester: "test.{extension}"
  test:
    dir: "test"
  ignore_patterns:
    - "*.bak"
    - "*.tmp"

languages:
  default: "cpp"
  cpp:
    name: "cpp"
    extension: "cpp"
  python:
    name: "python"
    extension: "py"

sites:
  atcoder:
    url: "https://atcoder.jp"
    problem_url: "{url}/contests/{contest}/tasks/{contest}_{problem}"
    submit_url: "{url}/contests/{contest}/tasks/{contest}_{problem}/submit"
"#;
        serde_yaml::from_str(config).unwrap()
    }

    #[test]
    fn test_new_contest() -> Result<()> {
        let config = create_test_config();
        let test_dir = tempdir().unwrap();
        std::env::set_current_dir(test_dir.path()).unwrap();

        let contest = Contest::new(&config, "a")?;
        assert_eq!(contest.active_contest_dir, PathBuf::from("active"));
        assert_eq!(contest.problem, Some("a".to_string()));
        assert_eq!(contest.language, Some("cpp".to_string()));
        Ok(())
    }

    #[test]
    fn test_set_language() -> Result<()> {
        let config = create_test_config();
        let test_dir = tempdir().unwrap();
        std::env::set_current_dir(test_dir.path()).unwrap();

        let mut contest = Contest::new(&config, "a")?;
        contest.set_language("python")?;
        assert_eq!(contest.language, Some("python".to_string()));

        // 存在しない言語を設定
        assert!(contest.set_language("invalid").is_err());
        Ok(())
    }

    #[test]
    fn test_set_site() -> Result<()> {
        let config = create_test_config();
        let test_dir = tempdir().unwrap();
        std::env::set_current_dir(test_dir.path()).unwrap();

        let mut contest = Contest::new(&config, "a")?;
        contest.set_site("atcoder")?;
        assert_eq!(contest.site, "atcoder");

        // 存在しないサイトを設定
        assert!(contest.set_site("invalid").is_err());
        Ok(())
    }

    #[test]
    fn test_get_problem_url() -> Result<()> {
        let config = create_test_config();
        let test_dir = tempdir().unwrap();
        std::env::set_current_dir(test_dir.path()).unwrap();

        let mut contest = Contest::new(&config, "a")?;
        contest.set_site("atcoder")?;
        contest.set_contest("abc123".to_string());

        let url = contest.get_problem_url("a")?;
        assert_eq!(url, "https://atcoder.jp/contests/abc123/tasks/abc123_a");
        Ok(())
    }

    #[test]
    fn test_create_problem_directory() -> Result<()> {
        let config = create_test_config();
        let test_dir = tempdir().unwrap();
        std::env::set_current_dir(test_dir.path()).unwrap();

        // テンプレートディレクトリの作成
        let template_dir = test_dir.path().join("templates").join("cpp");
        fs::create_dir_all(&template_dir)?;
        fs::write(template_dir.join("main.cpp"), "// Test template")?;

        // アクティブディレクトリの作成
        let active_dir = test_dir.path().join("active");
        fs::create_dir_all(&active_dir)?;

        let mut contest = Contest::new(&config, "a")?;
        contest.create_problem_directory("a")?;

        // ディレクトリとファイルの存在確認
        let problem_dir = active_dir.join("a");
        assert!(problem_dir.exists());
        assert!(problem_dir.join("main.cpp").exists());
        assert!(problem_dir.join("test").exists());

        // テンプレートの内容確認
        let content = fs::read_to_string(problem_dir.join("main.cpp"))?;
        assert_eq!(content, "// Test template");
        Ok(())
    }

    #[test]
    fn test_save_and_load() -> Result<()> {
        let config = create_test_config();
        let test_dir = tempdir().unwrap();
        std::env::set_current_dir(test_dir.path()).unwrap();

        // アクティブディレクトリの作成
        let active_dir = test_dir.path().join("active");
        fs::create_dir_all(&active_dir)?;

        let mut contest = Contest::new(&config, "a")?;
        contest.set_site("atcoder")?;
        contest.set_contest("abc123".to_string());
        contest.save()?;

        // 設定ファイルの存在確認
        let config_path = active_dir.join("contest.yaml");
        assert!(config_path.exists());

        // 設定の読み込みと確認
        let content = fs::read_to_string(config_path)?;
        let loaded: Contest = serde_yaml::from_str(&content)?;
        assert_eq!(loaded.site, "atcoder");
        assert_eq!(loaded.contest, "abc123");
        Ok(())
    }
} 