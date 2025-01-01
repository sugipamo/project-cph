use crate::error::{Result, ContestError};
use crate::config::{Config, TypedValue};
use serde::{Serialize, Deserialize};
use std::path::{PathBuf, Path};
use std::fs;
use std::io::BufRead;

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
    /// サステム設定パス
    const PATH_ACTIVE_DIR: &'static str = "system.contest_dir.active";
    const PATH_STORAGE_DIR: &'static str = "system.contest_dir.storage";
    const PATH_TEMPLATE_DIR: &'static str = "system.contest_dir.template";
    const PATH_TEMPLATE_PATTERN: &'static str = "system.templates.directory";
    const PATH_TEST_DIR: &'static str = "system.test.dir";
    const PATH_CONTEST_CONFIG: &'static str = "system.active_contest_yaml";

    /// 言語設定パス
    const PATH_DEFAULT_LANGUAGE: &'static str = "languages.default";
    const PATH_LANGUAGE_EXTENSION: &'static str = "languages.{}.extension";

    /// サイト設定パス
    const PATH_SITE_URL: &'static str = "sites.{}.url";
    const PATH_SITE_PROBLEM_URL: &'static str = "sites.{}.problem_url";
    const PATH_SITE_SUBMIT_URL: &'static str = "sites.{}.submit_url";

    /// サイト認証用のコンテストインスタンスを作成
    pub fn for_site_auth(config: &Config) -> Result<Self> {
        Ok(Self {
            active_contest_dir: PathBuf::new(),
            contest_id: String::new(),
            language: None,
            site_id: String::new(),
            workspace_dir: std::env::current_dir()
                .map_err(|e| ContestError::FileSystem(e.to_string()))?,
            config: config.clone(),
        })
    }

    /// 新しいコンテストインスタンスを作成
    /// 
    /// # 引数
    /// * `config` - 設定情報
    /// * `problem_id` - 問題ID（コンテストIDの抽出に使用）
    /// 
    /// # エラー
    /// - 設定の読み込みに失敗した場合
    /// - ディレクトリの作成に失敗した場合
    pub fn new(config: &Config, problem_id: &str) -> Result<Self> {
        // アクティブコンテストのディレクトリを設定から取得
        let active_dir = config.get::<String>(Self::PATH_ACTIVE_DIR)
            .map_err(|e| ContestError::config(format!("アクティブディレクトリの設定取得に失敗: {}", e)))?;
        
        let workspace_dir = std::env::current_dir()
            .map_err(|e| ContestError::fs(format!("カレントディレクトリの取得に失敗: {}", e)))?;
        let active_contest_dir = workspace_dir.join(&active_dir);

        if !active_contest_dir.exists() {
            println!("{}ディレクトリを作成します", active_dir);
            fs::create_dir_all(&active_contest_dir)
                .map_err(|e| ContestError::fs(
                    format!("{}ディレクトリの作成に失敗: {}", active_dir, e)
                ))?;
        }

        // コンテストIDを問題IDから抽出
        let contest_id = problem_id.split('_')
            .next()
            .unwrap_or(problem_id)
            .to_string();

        // コンテスト設定ファイル名を設定から取得
        let config_file = config.get::<String>(Self::PATH_CONTEST_CONFIG)
            .map_err(|e| ContestError::config(format!("コンテスト設定ファイル名の取得に失敗: {}", e)))?;
        let config_path = active_contest_dir.join(&config_file);

        if !config_path.exists() {
            // デフォルトのコンテスト設定を作成し、デフォルト言語を設定
            let mut contest = Self {
                active_contest_dir,
                workspace_dir,
                contest_id,
                language: None,
                site_id: String::new(),
                config: config.clone(),
            };

            // デフォルト言語を取得
            if let Ok(default_lang) = config.get::<String>(Self::PATH_DEFAULT_LANGUAGE) {
                contest.language = Some(default_lang);
            }

            return Ok(contest);
        }

        let content = fs::read_to_string(&config_path)
            .map_err(|e| ContestError::fs(format!("コンテスト設定ファイルの読み込みに失敗: {}", e)))?;
        let mut contest: Contest = serde_yaml::from_str(&content)
            .map_err(|e| ContestError::config(format!("{}の解析に失敗: {}", config_file, e)))?;
        
        contest.active_contest_dir = active_contest_dir;
        contest.workspace_dir = workspace_dir;
        contest.contest_id = contest_id;
        contest.config = config.clone();
        Ok(contest)
    }

    /// 現在の言語設定を取得
    /// 
    /// # 戻り値
    /// - 言語設定が存在する場合はその値
    /// - 存在しない場合はデフォルト言語
    pub fn get_solution_language(&self) -> Result<String> {
        // 1. 現在の言語設定を確認
        if let Some(lang) = &self.language {
            return Ok(lang.clone());
        }

        // 2. デフォルト言語を設定から取得
        self.get_system_config(Self::PATH_DEFAULT_LANGUAGE)
            .map_err(|e| ContestError::language("デフォルト言語の取得に失敗".into()))
    }

    /// コンテストの設定を保存
    pub fn save(&self) -> Result<()> {
        // コンテスト設定ファイル名を設定から取得
        let config_file = self.get_system_config(Self::PATH_CONTEST_CONFIG)
            .map_err(|e| ContestError::config(format!("コンテスト設定ファイル名の取得に失敗: {}", e)))?;
        let config_path = self.active_contest_dir.join(&config_file);

        let content = serde_yaml::to_string(&self)
            .map_err(|e| ContestError::config(format!("コンテスト設定のシリアライズに失敗: {}", e)))?;
        fs::write(&config_path, content)
            .map_err(|e| ContestError::fs(format!("コンテスト設定ファイルの書き込みに失敗: {}", e)))?;

        // 既存のファイルを移動
        self.move_files_to_contests()?;

        Ok(())
    }

    /// 言語固有の設定を取得
    /// 
    /// # 引数
    /// * `config_path` - 設定値のパス
    /// 
    /// # 型パラメータ
    /// * `T` - 取得する設定値の型
    /// 
    /// # エラー
    /// - 設定が存在しない場合
    /// - 型変換に失敗した場合
    fn get_language_config<T: TypedValue>(&self, config_path: &str) -> Result<T> {
        // 1. 現在の言語設定を取得
        let language = if let Some(lang) = &self.language {
            lang.clone()
        } else {
            self.config.get::<String>("languages.default")
                .map_err(|e| ContestError::Language(e.to_string()))?
        };

        // 2. 言語固有の設定を試す
        self.config.get::<T>(&format!("languages.{}.{}", language, config_path))
            .or_else(|_| self.config.get::<T>(config_path))
            .map_err(|e| ContestError::Config(e.to_string()).into())
    }

    /// 問題ファイルのパスを取得
    /// 
    /// # 引数
    /// * `problem_id` - 問題ID
    /// * `file_type` - ファイルの種類（solution, generator, tester）
    fn get_problem_file_path(&self, problem_id: &str, file_type: &str) -> Result<PathBuf> {
        let language = self.language.as_ref()
            .ok_or_else(|| ContestError::language("言語が設定されていません".into()))?;

        // 拡張子を取得
        let extension_path = Self::PATH_LANGUAGE_EXTENSION.replace("{}", language);
        let extension = self.config.get::<String>(&extension_path)
            .map_err(|e| ContestError::language(format!("言語{}の拡張子取得に失敗: {}", language, e)))?;

        // パターンを取得
        let pattern = self.get_system_config(&format!("system.templates.patterns.{}", file_type))
            .map_err(|e| ContestError::config(format!("ファイルパターンの取得に失敗: {}", e)))?;

        let file_name = pattern.replace("{extension}", &extension);
        Ok(self.active_contest_dir.join(problem_id).join(file_name))
    }

    /// ソリューションファイルのパスを取得
    pub fn get_solution_path(&self, problem_id: &str) -> Result<PathBuf> {
        self.get_problem_file_path(problem_id, "solution")
            .map_err(|e| ContestError::fs(
                format!("ソリューションファイルのパス取得に失敗\n問題ID: {}\nエラー: {}", problem_id, e)
            ).into())
    }

    /// ジェネレータファイルのパスを取得
    pub fn get_generator_path(&self, problem_id: &str) -> Result<PathBuf> {
        self.get_problem_file_path(problem_id, "generator")
            .map_err(|e| ContestError::fs(
                format!("ジェネレータファイルのパス取得に失敗\n問題ID: {}\nエラー: {}", problem_id, e)
            ).into())
    }

    /// テスターファイルのパスを取得
    pub fn get_tester_path(&self, problem_id: &str) -> Result<PathBuf> {
        self.get_problem_file_path(problem_id, "tester")
            .map_err(|e| ContestError::fs(
                format!("テスターファイルのパス取得に失敗\n問題ID: {}\nエラー: {}", problem_id, e)
            ).into())
    }

    /// コンテストIDを設定
    pub fn set_contest(&mut self, contest_id: String) {
        self.contest_id = contest_id;
    }

    /// 使用言語を設定
    /// 
    /// # エラー
    /// - 指定された言語が存在しない場合
    pub fn set_language(&mut self, language: &str) -> Result<()> {
        // 1. エイリアス解決を試みる
        let resolved_language = self.config.get_with_alias::<String>(&format!("{}.name", language))
            .unwrap_or_else(|_| language.to_string());

        // 2. 言語の存在確認（拡張子の取得で確認）
        let extension_path = Self::PATH_LANGUAGE_EXTENSION.replace("{}", &resolved_language);
        match self.config.get::<String>(&extension_path) {
            Ok(_) => {
                self.language = Some(resolved_language.clone());
                Ok(())
            },
            Err(e) => Err(ContestError::language(format!("言語{}は存在しません: {}", resolved_language, e)).into()),
        }
    }

    /// サイトを設定
    /// 
    /// # エラー
    /// - 指定されたサイトが存在しない場合
    pub fn set_site(&mut self, site_id: &str) -> Result<()> {
        // サイトの存在確認
        let problem_url_path = Self::PATH_SITE_PROBLEM_URL.replace("{}", site_id);
        self.config.get::<String>(&problem_url_path)
            .map_err(|e| ContestError::site(format!("サイト{}は存在しません: {}", site_id, e)))?;
        self.site_id = site_id.to_string();
        Ok(())
    }

    /// ディレクトリ内容を再帰的にコピー
    fn copy_dir_contents(&self, source: &Path, target: &Path) -> Result<()> {
        for entry in fs::read_dir(source)
            .map_err(|e| ContestError::fs(format!("ディレクトリの読み取りに失敗: {}", e)))? {
            let entry = entry.map_err(|e| ContestError::fs(format!("ディレクトリエントリの読み取りに失敗: {}", e)))?;
            let file_type = entry.file_type()
                .map_err(|e| ContestError::fs(format!("ファイルタイプの取得に失敗: {}", e)))?;
            let source_path = entry.path();
            let file_name = entry.file_name();
            let target_path = target.join(&file_name);

            if file_type.is_dir() {
                if !target_path.exists() {
                    println!("ディレクトリを作成: {}", target_path.display());
                    fs::create_dir_all(&target_path)
                        .map_err(|e| ContestError::fs(format!("ディレクトリの作成に失敗: {}", e)))?;
                }
                self.copy_dir_contents(&source_path, &target_path)?;
            } else {
                if !target_path.exists() {
                    println!("ファイルをコピー: {} -> {}", source_path.display(), target_path.display());
                    fs::copy(&source_path, &target_path)
                        .map_err(|e| ContestError::fs(format!("ファイルのコピーに失敗: {}", e)))?;
                } else {
                    println!("ファイルはすでに存在します（スキップ）: {}", target_path.display());
                }
            }
        }
        Ok(())
    }

    /// ファイルをcontestsディレクトリに移動
    fn move_files_to_contests(&self) -> Result<()> {
        // 1. .moveignoreの読み込み
        let _ignore_patterns = self.read_moveignore()?;
        
        // 2. コンテストの保存先ディレクトリを設定から取得
        let storage_base = self.get_system_config(Self::PATH_STORAGE_DIR)
            .map_err(|e| ContestError::config(format!("コンテスト保存先ディレクトリの設定取得に失敗: {}", e)))?;

        let contests_dir = self.workspace_dir.join(&storage_base);

        // 3. 保存先ディレクトリの作成
        if !contests_dir.exists() {
            fs::create_dir_all(&contests_dir)
                .map_err(|e| ContestError::fs(format!("コンテスト保存先ディレクトリの作成に失敗: {}", e)))?;
        }

        // 4. コンテスト用のディレクトリを作成
        let contest_dir = contests_dir.join(&self.contest_id);
        if !contest_dir.exists() {
            fs::create_dir_all(&contest_dir)
                .map_err(|e| ContestError::fs(format!("コンテストディレクトリの作成に失敗: {}", e)))?;
        }

        Ok(())
    }

    /// .moveignoreファイルを読み込む
    fn read_moveignore(&self) -> Result<Vec<String>> {
        let moveignore_path = self.active_contest_dir.join(".moveignore");
        let mut patterns = vec![];

        // .moveignoreが存在しない場合は設定から取得
        if !moveignore_path.exists() {
            let config_file = self.get_system_config(Self::PATH_CONTEST_CONFIG)
                .map_err(|e| ContestError::config(format!("コンテスト設定ファイル名の取得に失敗: {}", e)))?;

            let mut ignore_patterns = vec![config_file];
            if let Ok(additional_patterns) = self.get_system_config::<Vec<String>>("system.ignore_patterns") {
                ignore_patterns.extend(additional_patterns);
            }
            return Ok(ignore_patterns);
        }

        // ファイルを読み込む
        let file = fs::File::open(moveignore_path)
            .map_err(|e| ContestError::fs(format!(".moveignoreファイルの読み込みに失敗: {}", e)))?;
        let reader = std::io::BufReader::new(file);

        for line in reader.lines() {
            let line = line.map_err(|e| ContestError::fs(format!(".moveignoreファイルの行の読み込みに失敗: {}", e)))?;
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
            .ok_or_else(|| ContestError::language("言語が設定されていません".into()))?;

        // テンプレートディレクトリのパスを生成
        let template_pattern = self.get_system_config(Self::PATH_TEMPLATE_PATTERN)
            .map_err(|e| ContestError::config(format!("テンプレートパターンの取得に失敗: {}", e)))?;
        let template_base = self.get_system_config(Self::PATH_TEMPLATE_DIR)
            .map_err(|e| ContestError::config(format!("テンプレートディレクトリの設定取得に失敗: {}", e)))?;
        
        let template_dir_name = template_pattern.replace("{name}", language);
        let template_dir = self.workspace_dir.join(&template_base).join(template_dir_name);

        // 問題ディレクトリを作成
        let problem_dir = self.active_contest_dir.join(problem_id);
        if !problem_dir.exists() {
            fs::create_dir_all(&problem_dir)
                .map_err(|e| ContestError::fs(format!("問題ディレクトリの作成に失敗: {}", e)))?;
        }

        // テストディレクトリを作成
        let test_dir = self.get_test_dir(problem_id)?;
        if !test_dir.exists() {
            fs::create_dir_all(&test_dir)
                .map_err(|e| ContestError::fs(format!("テストディレクトリの作成に失敗: {}", e)))?;
        }

        if !template_dir.exists() {
            return Err(ContestError::fs(
                format!("テンプレートディレクトリが見つかりません: {}", template_dir.display())
            ).into());
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
        let pattern_path = match url_type {
            "problem" => Self::PATH_SITE_PROBLEM_URL,
            "submit" => Self::PATH_SITE_SUBMIT_URL,
            _ => return Err(ContestError::site(format!("不正なURL種別: {}", url_type)).into()),
        };

        let pattern = self.get_site_config(pattern_path)?;
        let site_url = self.get_site_config(Self::PATH_SITE_URL)?;
        
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
        let test_dir = self.get_system_config(Self::PATH_TEST_DIR)
            .map_err(|e| ContestError::config(format!("テストディレクトリの設定取得に失敗: {}", e)))?;
        Ok(self.active_contest_dir.join(problem_id).join(test_dir))
    }

    /// システム設定を取得
    fn get_system_config<T: TypedValue>(&self, path: &str) -> Result<T> {
        self.config.get(path)
            .map_err(|e| ContestError::config(format!("システム設定の取得に失敗: {}", e)))
    }

    /// 言語設定を取得
    fn get_language_config<T: TypedValue>(&self, path: &str) -> Result<T> {
        let language = self.get_solution_language()?;
        let full_path = path.replace("{}", &language);
        
        self.config.get(&full_path)
            .map_err(|e| ContestError::language(format!("言語設定の取得に失敗: {}", e)))
    }

    /// サイト設定を取得
    fn get_site_config<T: TypedValue>(&self, path: &str) -> Result<T> {
        let full_path = path.replace("{}", &self.site_id);
        
        self.config.get(&full_path)
            .map_err(|e| ContestError::site(format!("サイト設定の取得に失敗: {}", e)))
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    // TODO: テストの実装
} 