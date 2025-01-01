use crate::config::{Config, TypedValue};
use serde::{Serialize, Deserialize};
use std::path::{PathBuf, Path};
use std::fs;
use std::io::BufRead;

type Result<T> = std::result::Result<T, String>;

/// コンテスト情報を管理する構造体
/// 
/// この構造体は以下の責務を持ちます：
/// - コンテスト情報の管理（ID、言語、サイト）
/// - ファイルシステム操作（テンプレート、移動、コピー）
/// - 設定管理（読み込み、保存、アクセス）
/// - URL生成（問題URL、提出URL）
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Contest {
    /// アクティブなコンテストのディレクトリ
    #[serde(default)]
    pub active_contest_dir: PathBuf,

    /// コンテストID
    pub contest_id: String,

    /// 使用言語
    pub language: Option<String>,

    /// サイトID（例: atcoder, codeforces）
    pub site_id: String,

    /// ワークスペースのルートディレクトリ
    #[serde(skip)]
    workspace_dir: PathBuf,

    /// 設定情報
    #[serde(skip)]
    config: Config,
}

impl Contest {
    /// サイト認証用のコンテストインスタンスを作成
    pub fn for_site_auth(config: &Config) -> Result<Self> {
        Ok(Self {
            active_contest_dir: PathBuf::new(),
            contest_id: String::new(),
            language: None,
            site_id: String::new(),
            workspace_dir: std::env::current_dir()
                .map_err(|e| format!("カレントディレクトリの取得に失敗: {}", e))?,
            config: config.clone(),
        })
    }

    /// 新しいコンテストインスタンスを作成
    pub fn new(config: &Config, problem_id: &str) -> Result<Self> {
        let active_dir = config.get::<String>("system.contest_dir.active")
            .map_err(|e| format!("アクティブディレクトリの設定取得に失敗: {}", e))?;
        
        let workspace_dir = std::env::current_dir()
            .map_err(|e| format!("カレントディレクトリの取得に失敗: {}", e))?;
        let active_contest_dir = workspace_dir.join(&active_dir);

        if !active_contest_dir.exists() {
            println!("{}ディレクトリを作成します", active_dir);
            fs::create_dir_all(&active_contest_dir)
                .map_err(|e| format!("{}ディレクトリの作成に失敗: {}", active_dir, e))?;
        }

        let contest_id = problem_id.split('_')
            .next()
            .unwrap_or(problem_id)
            .to_string();

        let config_file = config.get::<String>("system.active_contest_yaml")
            .map_err(|e| format!("コンテスト設定ファイル名の取得に失敗: {}", e))?;
        let config_path = active_contest_dir.join(&config_file);

        if !config_path.exists() {
            let mut contest = Self {
                active_contest_dir,
                workspace_dir,
                contest_id,
                language: None,
                site_id: String::new(),
                config: config.clone(),
            };

            if let Ok(default_lang) = config.get::<String>("languages.default") {
                contest.language = Some(default_lang);
            }

            return Ok(contest);
        }

        let content = fs::read_to_string(&config_path)
            .map_err(|e| format!("コンテスト設定ファイルの読み込みに失敗: {}", e))?;
        let mut contest: Contest = serde_yaml::from_str(&content)
            .map_err(|e| format!("{}の解析に失敗: {}", config_file, e))?;
        
        contest.active_contest_dir = active_contest_dir;
        contest.workspace_dir = workspace_dir;
        contest.contest_id = contest_id;
        contest.config = config.clone();
        Ok(contest)
    }

    /// 現在の言語設定を取得
    pub fn get_solution_language(&self) -> Result<String> {
        if let Some(lang) = &self.language {
            return Ok(lang.clone());
        }

        self.config.get::<String>("languages.default")
            .map_err(|e| format!("デフォルト言語の取得に失敗: {}", e))
    }

    /// コンテストの設定を保存
    pub fn save(&self) -> Result<()> {
        let config_file = self.config.get::<String>("system.active_contest_yaml")
            .map_err(|e| format!("コンテスト設定ファイル名の取得に失敗: {}", e))?;
        let config_path = self.active_contest_dir.join(&config_file);

        let content = serde_yaml::to_string(&self)
            .map_err(|e| format!("コンテスト設定のシリアライズに失敗: {}", e))?;
        fs::write(&config_path, content)
            .map_err(|e| format!("コンテスト設定ファイルの書き込みに失敗: {}", e))?;

        self.move_files_to_contests()?;

        Ok(())
    }

    /// 問題ファイルのパスを取得
    fn get_problem_file_path(&self, problem_id: &str, file_type: &str) -> Result<PathBuf> {
        let language = self.language.as_ref()
            .ok_or_else(|| "言語が設定されていません".to_string())?;

        let extension = self.config.get::<String>(&format!("languages.{}.extension", language))
            .map_err(|e| format!("言語{}の拡張子取得に失敗: {}", language, e))?;

        let pattern = self.config.get::<String>(&format!("system.templates.patterns.{}", file_type))
            .map_err(|e| format!("ファイルパターンの取得に失敗: {}", e))?;

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

    /// コンテストIDを設定
    pub fn set_contest(&mut self, contest_id: String) {
        self.contest_id = contest_id;
    }

    /// 使用言語を設定
    pub fn set_language(&mut self, language: &str) -> Result<()> {
        let resolved_language = self.config.get_with_alias::<String>(&format!("{}.name", language))
            .unwrap_or_else(|_| language.to_string());

        match self.config.get::<String>(&format!("languages.{}.extension", resolved_language)) {
            Ok(_) => {
                self.language = Some(resolved_language);
                Ok(())
            },
            Err(e) => Err(format!("言語{}は存在しません: {}", resolved_language, e)),
        }
    }

    /// サイトを設定
    pub fn set_site(&mut self, site_id: &str) -> Result<()> {
        self.config.get::<String>(&format!("sites.{}.problem_url", site_id))
            .map_err(|e| format!("サイト{}は存在しません: {}", site_id, e))?;
        self.site_id = site_id.to_string();
        Ok(())
    }

    /// ディレクトリ内容を再帰的にコピー
    fn copy_dir_contents(&self, source: &Path, target: &Path) -> Result<()> {
        for entry in fs::read_dir(source)
            .map_err(|e| format!("ディレクトリの読み取りに失敗: {}", e))? {
            let entry = entry.map_err(|e| format!("ディレクトリエントリの読み取りに失敗: {}", e))?;
            let file_type = entry.file_type()
                .map_err(|e| format!("ファイルタイプの取得に失敗: {}", e))?;
            let source_path = entry.path();
            let file_name = entry.file_name();
            let target_path = target.join(&file_name);

            if file_type.is_dir() {
                if !target_path.exists() {
                    println!("ディレクトリを作成: {}", target_path.display());
                    fs::create_dir_all(&target_path)
                        .map_err(|e| format!("ディレクトリの作成に失敗: {}", e))?;
                }
                self.copy_dir_contents(&source_path, &target_path)?;
            } else {
                if !target_path.exists() {
                    println!("ファイルをコピー: {} -> {}", source_path.display(), target_path.display());
                    fs::copy(&source_path, &target_path)
                        .map_err(|e| format!("ファイルのコピーに失敗: {}", e))?;
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
        
        let storage_base = self.config.get::<String>("system.contest_dir.storage")
            .map_err(|e| format!("コンテスト保存先ディレクトリの設定取得に失敗: {}", e))?;

        let contests_dir = self.workspace_dir.join(&storage_base);

        if !contests_dir.exists() {
            fs::create_dir_all(&contests_dir)
                .map_err(|e| format!("コンテスト保存先ディレクトリの作成に失敗: {}", e))?;
        }

        let contest_dir = contests_dir.join(&self.contest_id);
        if !contest_dir.exists() {
            fs::create_dir_all(&contest_dir)
                .map_err(|e| format!("コンテストディレクトリの作成に失敗: {}", e))?;
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
            .ok_or_else(|| "言語が設定されていません".to_string())?;

        let template_pattern = self.config.get::<String>("system.templates.directory")
            .map_err(|e| format!("テンプレートパターンの取得に失敗: {}", e))?;
        let template_base = self.config.get::<String>("system.contest_dir.template")
            .map_err(|e| format!("テンプレートディレクトリの設定取得に失敗: {}", e))?;
        
        let template_dir_name = template_pattern.replace("{name}", language);
        let template_dir = self.workspace_dir.join(&template_base).join(template_dir_name);

        let problem_dir = self.active_contest_dir.join(problem_id);
        if !problem_dir.exists() {
            fs::create_dir_all(&problem_dir)
                .map_err(|e| format!("問題ディレクトリの作成に失敗: {}", e))?;
        }

        let test_dir = self.get_test_dir(problem_id)?;
        if !test_dir.exists() {
            fs::create_dir_all(&test_dir)
                .map_err(|e| format!("テストディレクトリの作成に失敗: {}", e))?;
        }

        if !template_dir.exists() {
            return Err(format!("テンプレートディレクトリが見つかりません: {}", template_dir.display()));
        }

        println!("テンプレートをコピーしています...");
        println!("From: {}", template_dir.display());
        println!("To: {}", problem_dir.display());

        self.copy_dir_contents(&template_dir, &problem_dir)?;

        println!("テンプレートのコピーが完了しました");
        Ok(())
    }

    /// サイトのURLを生成
    fn get_site_url(&self, url_type: &str, problem_id: &str) -> Result<String> {
        let pattern = self.config.get::<String>(&format!("sites.{}.{}_url", self.site_id, url_type))
            .map_err(|e| format!("サイトURLパターンの取得に失敗: {}", e))?;
        
        let site_url = self.config.get::<String>(&format!("sites.{}.url", self.site_id))
            .map_err(|e| format!("サイトURLの取得に失敗: {}", e))?;

        Ok(pattern
            .replace("{url}", &site_url)
            .replace("{contest_id}", &self.contest_id)
            .replace("{problem_id}", problem_id))
    }

    /// 問題のURLを取得
    pub fn get_problem_url(&self, problem_id: &str) -> Result<String> {
        self.get_site_url("problem", problem_id)
    }

    /// 提出のURLを取得
    pub fn get_submit_url(&self, problem_id: &str) -> Result<String> {
        self.get_site_url("submit", problem_id)
    }

    /// テストを実行
    pub fn run_test(&self, problem_id: &str) -> Result<()> {
        println!("TODO: Implement run_test for problem {}", problem_id);
        Ok(())
    }

    /// テストケースを生成
    pub fn generate_test(&self, problem_id: &str) -> Result<()> {
        println!("TODO: Implement generate_test for problem {}", problem_id);
        Ok(())
    }

    /// テストディレクトリのパスを取得
    pub fn get_test_dir(&self, problem_id: &str) -> Result<PathBuf> {
        let test_dir = self.config.get::<String>("system.test.dir")
            .map_err(|e| format!("テストディレクトリの設定取得に失敗: {}", e))?;
        Ok(self.active_contest_dir.join(problem_id).join(test_dir))
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    // TODO: テストの実装
} 