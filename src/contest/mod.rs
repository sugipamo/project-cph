use crate::{cli::Site, error::Result, config::Config};
use serde::{Serialize, Deserialize};
use std::path::{PathBuf, Path};
use std::fs;
use std::io::BufRead;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Contest {
    #[serde(default)]
    pub active_contest_dir: PathBuf,
    pub contest_id: String,
    pub language: Option<String>,
    pub site: Site,
    #[serde(skip)]
    workspace_dir: PathBuf,
    #[serde(skip)]
    config: Config,
}

impl Default for Contest {
    fn default() -> Self {
        // 1. 設定の読み込み
        let config = Config::load().unwrap_or_else(|e| {
            eprintln!("警告: 設定の読み込みに失敗しました: {}", e);
            Config::default()
        });

        // 2. アクティブディレクトリの設定を取得
        let active_dir = config.get::<String>("system.contest_dir.active")
            .or_else(|_| config.get_with_alias::<String>("contest_dir.active"))
            .unwrap_or_else(|e| {
                eprintln!("警告: アクティブディレクトリの設定の読み込みに失敗しました: {}", e);
                "contests/active".to_string()
            });

        // 3. デフォルト言語の設定を試みる
        let language = config.get::<String>("languages.default")
            .or_else(|_| config.get_with_alias::<String>("default_language"))
            .ok();

        Contest {
            active_contest_dir: PathBuf::from(active_dir),
            contest_id: String::new(),
            language,
            site: Site::AtCoder,
            workspace_dir: PathBuf::new(),
            config,
        }
    }
}

impl Contest {
    pub fn new(config: &Config, problem_id: &str) -> Result<Self> {
        // アクティブコンテストのディレクトリを設定から取得
        let active_dir = config.get::<String>("system.contest_dir.active")?;
        
        let workspace_dir = std::env::current_dir()?;
        let active_contest_dir = workspace_dir.join(&active_dir);

        if !active_contest_dir.exists() {
            println!("{}ディレクトリを作成します", active_dir);
            fs::create_dir_all(&active_contest_dir)
                .map_err(|e| format!("{}ディレクトリの作成に失敗しました: {}", active_dir, e))?;
        }

        // コンテストIDを問題IDから抽出
        let contest_id = problem_id.split('_')
            .next()
            .unwrap_or(problem_id)
            .to_string();

        // コンテスト設定ファイル名を設定から取得
        let config_file = config.get::<String>("system.active_contest_yaml")?;
        let config_path = active_contest_dir.join(&config_file);

        if !config_path.exists() {
            // デフォルトのコンテスト設定を作成し、デフォルト言語を設定
            let mut contest = Self {
                active_contest_dir,
                workspace_dir,
                contest_id,
                language: None,
                site: Site::AtCoder,
                config: config.clone(),
            };

            // デフォルト言語を取得
            if let Ok(default_lang) = config.get::<String>("languages.default") {
                contest.language = Some(default_lang);
            }

            return Ok(contest);
        }

        let content = fs::read_to_string(&config_path)?;
        let mut contest: Contest = serde_yaml::from_str(&content)
            .map_err(|e| format!("{}の解析に失敗しました: {}", config_file, e))?;
        
        contest.active_contest_dir = active_contest_dir;
        contest.workspace_dir = workspace_dir;
        contest.contest_id = contest_id;
        contest.config = config.clone();
        Ok(contest)
    }

    pub fn get_solution_language(&self) -> Result<String> {
        // 1. 現在の言語設定を確認
        if let Some(lang) = &self.language {
            return Ok(lang.clone());
        }

        // 2. デフォルト言語を設定から取得
        Ok(self.config.get::<String>("languages.default")?)
    }

    pub fn save(&self) -> Result<()> {
        // コンテスト設定ファイル名を設定から取得
        let config_file = self.config.get::<String>("system.active_contest_yaml")?;
        let config_path = self.active_contest_dir.join(&config_file);

        let content = serde_yaml::to_string(&self)
            .map_err(|e| format!("{}の保存に失敗しました: {}", config_file, e))?;
        fs::write(config_path, content)?;

        // 既存のファイルを移動
        self.move_files_to_contests()?;

        Ok(())
    }

    // 共通の問題ファイルパス取得処理
    fn get_problem_file_path(&self, problem_id: &str, file_type: &str) -> Result<PathBuf> {
        // 1. 現在の言語設定を取得
        let language = if let Some(lang) = &self.language {
            lang.clone()
        } else {
            self.config.get::<String>("languages.default")?
        };
        
        // 2. 言語の存在確認と拡張子の取得
        let extension = self.config.get_with_alias::<String>(&format!("{}.extension", language))
            .or_else(|_| self.config.get::<String>(&format!("languages.{}.extension", language)))?;

        // 3. ファイル名のパターンを取得
        let pattern = self.config.get::<String>(&format!("system.templates.patterns.{}", file_type))?;
        
        // パターンの{extension}を実際の拡張子に置換
        let file_name = pattern.replace("{extension}", &extension);

        // 問題ディレクトリのパスを生成
        let problem_dir = self.active_contest_dir.join(problem_id);

        // 生成したファイル名でパスを生成
        Ok(problem_dir.join(file_name))
    }

    // solution.[ext]のパスを取得
    pub fn get_solution_path(&self, problem_id: &str) -> Result<PathBuf> {
        self.get_problem_file_path(problem_id, "solution")
            .map_err(|e| format!("ソリューションファイルのパス取得に失敗しました。\n問題ID: {}\nエラー: {}", problem_id, e).into())
    }

    // generator.[ext]のパスを取得
    pub fn get_generator_path(&self, problem_id: &str) -> Result<PathBuf> {
        self.get_problem_file_path(problem_id, "generator")
            .map_err(|e| format!("ジェネレータファイルのパス取得に失敗しました。\n問題ID: {}\nエラー: {}", problem_id, e).into())
    }

    // tester.[ext]のパスを取得
    pub fn get_tester_path(&self, problem_id: &str) -> Result<PathBuf> {
        self.get_problem_file_path(problem_id, "tester")
            .map_err(|e| format!("テスターファイルのパス取得に失敗しました。\n問題ID: {}\nエラー: {}", problem_id, e).into())
    }

    pub fn set_contest(&mut self, contest_id: String) {
        self.contest_id = contest_id;
    }

    pub fn set_language(&mut self, language: &str) -> Result<()> {
        // 1. エイリアス解決を試みる
        let resolved_language = self.config.get_with_alias::<String>(&format!("{}.name", language))
            .unwrap_or_else(|_| language.to_string());

        // 2. 言語の存在確認
        match self.config.get::<String>(&format!("languages.{}.extension", resolved_language)) {
            Ok(_) => {
                self.language = Some(resolved_language.clone());
                Ok(())
            },
            Err(e) => Err(e.into()),
        }
    }

    pub fn set_site(&mut self, site_name: &str) -> Result<()> {
        // 1. エイリアス解決を試みる
        let resolved_site = self.config.get_with_alias::<String>(&format!("{}.name", site_name))
            .unwrap_or_else(|_| site_name.to_string());

        // 2. サイトの存在確認と設定
        self.config.get::<String>(&format!("sites.{}.problem_url", resolved_site))?;
        
        // 3. サイトの設定
        self.site = match resolved_site.to_lowercase().as_str() {
            "atcoder" => Site::AtCoder,
            _ => return Err(format!("サイト '{}' はサポートされていません", site_name).into()),
        };
        Ok(())
    }

    // ティレクトリ内容のコピー（再帰的）
    fn copy_dir_contents(&self, source: &Path, target: &Path) -> Result<()> {
        for entry in fs::read_dir(source)? {
            let entry = entry?;
            let file_type = entry.file_type()?;
            let source_path = entry.path();
            let file_name = entry.file_name();
            let target_path = target.join(&file_name);

            if file_type.is_dir() {
                if !target_path.exists() {
                    println!("ディレクトリを作成: {}", target_path.display());
                    fs::create_dir_all(&target_path)?;
                }
                self.copy_dir_contents(&source_path, &target_path)?;
            } else {
                if !target_path.exists() {
                    println!("ファイルをコピー: {} -> {}", source_path.display(), target_path.display());
                    fs::copy(&source_path, &target_path)?;
                } else {
                    println!("ファイルはすでに存在します（スキップ）: {}", target_path.display());
                }
            }
        }
        Ok(())
    }

    // ファイルを contests ディレクトリに移動
    fn move_files_to_contests(&self) -> Result<()> {
        // 1. .moveignoreの読み込み
        let _ignore_patterns = self.read_moveignore()?;
        
        // 2. コンテストの保存先ディレクトリを設定から取得
        let storage_base = self.config.get::<String>("system.contest_dir.storage")
            .or_else(|_| self.config.get_with_alias::<String>("contest_dir.storage"))?;

        let contests_dir = self.workspace_dir.join(&storage_base);

        // 3. 保存先ディレクトリの作成
        if !contests_dir.exists() {
            fs::create_dir_all(&contests_dir)?;
        }

        // 4. コンテスト用のディレクトリを作成
        let contest_dir = contests_dir.join(&self.contest_id);
        if !contest_dir.exists() {
            fs::create_dir_all(&contest_dir)?;
        }

        Ok(())
    }

    // .moveignoreファイルを読み込む
    fn read_moveignore(&self) -> Result<Vec<String>> {
        let moveignore_path = self.active_contest_dir.join(".moveignore");
        let mut patterns = vec![];

        // .moveignoreが存在しない場合は設定から取得
        if !moveignore_path.exists() {
            // コンテスト設定ファイル名を取得
            let config_file = self.config.get::<String>("system.active_contest_yaml")?;

            // 無視パターンを設定から取得
            let mut ignore_patterns = vec![config_file];
            if let Ok(additional_patterns) = self.config.get::<Vec<String>>("system.ignore_patterns") {
                ignore_patterns.extend(additional_patterns);
            }
            return Ok(ignore_patterns);
        }

        // ファイルを読み込む
        let file = fs::File::open(moveignore_path)?;
        let reader = std::io::BufReader::new(file);

        for line in reader.lines() {
            let line = line?;
            let line = line.trim();
            
            // 空行とコメントをスキップ
            if line.is_empty() || line.starts_with('#') {
                continue;
            }

            patterns.push(line.to_string());
        }

        Ok(patterns)
    }

    // ファイルが.moveignoreパターンに一致するかチェック
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

    // 問題ディレクトリの作成とテンプレートのコピーを行う
    pub fn create_problem_directory(&self, problem_id: &str) -> Result<()> {
        let language = self.language.as_ref()
            .ok_or_else(|| "言語が設定されていません".to_string())?;

        // 問題ディレクトリのパスを生成
        let problem_dir = self.active_contest_dir.join(problem_id);
        if !problem_dir.exists() {
            fs::create_dir_all(&problem_dir)?;
        }

        // テストディレクトリ名を設定から取得
        let test_dir_name = self.config.get::<String>("system.test.dir")?;
        let test_dir = problem_dir.join(test_dir_name);
        if !test_dir.exists() {
            fs::create_dir_all(&test_dir)?;
        }

        // テンプレートディレクトリのパターンを設定から取得
        let template_pattern = self.config.get::<String>("system.templates.directory")?;
        let template_base = self.config.get::<String>("system.contest_dir.template")?;
        
        // パターンの{name}を言語名に置換
        let template_dir_name = template_pattern.replace("{name}", language);
        let template_dir = self.workspace_dir.join(&template_base).join(template_dir_name);

        if !template_dir.exists() {
            return Err(format!("テンプレートディレクトリが見つかりません: {}", template_dir.display()).into());
        }

        println!("テンプレートをコピーしています...");
        println!("From: {}", template_dir.display());
        println!("To: {}", problem_dir.display());

        // ディレクトリ内容を再帰的にコピー
        self.copy_dir_contents(&template_dir, &problem_dir)?;

        println!("テンプレートのコピーが完了しました");
        Ok(())
    }
} 