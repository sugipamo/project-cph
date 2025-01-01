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
}

impl Default for Contest {
    fn default() -> Self {
        // config/mod.rsを使用して設定を取得
        let config = Config::builder()
            .unwrap_or_else(|_| Config::builder().unwrap());  // エラー時は空の設定を使用

        // デフォルトのアクティブディレクトリを設定から取得
        let active_dir = config.get::<String>("system.contest_dir.active")
            .unwrap_or_else(|_| "active_contest".to_string());

        // デフォルトのサイトを設定から取得（エイリアス解決を使用）
        let default_site = config.get_with_alias::<String>("sites.default.name")
            .map(|site| match site.to_lowercase().as_str() {
                "atcoder" => Site::AtCoder,
                _ => Site::AtCoder // デフォルトはAtCoder
            })
            .unwrap_or(Site::AtCoder);

        Self {
            active_contest_dir: PathBuf::from(active_dir),
            contest_id: String::new(),
            language: None,
            site: default_site,
            workspace_dir: PathBuf::new(),
        }
    }
}

impl Contest {
    pub fn new(current_dir: PathBuf) -> Result<Self> {
        // config/mod.rsを使用して設定を取得
        let config = Config::builder()
            .map_err(|e| format!("設定の読み込みに失敗しました: {}", e))?;

        // アクティブコンテストのディレクトリを設定から取得
        let active_base = config.get::<String>("system.contest_dir.active")
            .unwrap_or_else(|_| "active_contest".to_string());
        let active_dir = current_dir.join(&active_base);

        if !active_dir.exists() {
            println!("{}ディレクトリを作成します", active_base);
            fs::create_dir_all(&active_dir)
                .map_err(|e| format!("{}ディレクトリの作成に失敗しました: {}", active_base, e))?;
        }

        // コンテスト設定ファイル名を設定から取得
        let config_file = config.get::<String>("system.active_contest_yaml")
            .unwrap_or_else(|_| "contests.yaml".to_string());
        let config_path = active_dir.join(&config_file);

        if !config_path.exists() {
            // デフォルトのコンテスト設定を作成し、デフォルト言語を設定
            let mut contest = Self::default();
            contest.active_contest_dir = active_dir;
            contest.workspace_dir = current_dir.clone();

            // デフォルト言語を取得
            if let Ok(default_lang) = config.get::<String>("languages.default") {
                contest.language = Some(default_lang);
            }

            return Ok(contest);
        }

        let content = fs::read_to_string(&config_path)?;
        let mut contest: Contest = serde_yaml::from_str(&content)
            .map_err(|e| format!("{}の解析に失敗しました: {}", config_file, e))?;
        
        contest.active_contest_dir = active_dir;
        contest.workspace_dir = current_dir;
        Ok(contest)
    }

    pub fn save(&self) -> Result<()> {
        // config/mod.rsを使用して設定を取得
        let config = Config::builder()
            .map_err(|e| format!("設定の読み込みに失敗しました: {}", e))?;

        // コンテスト設定ファイル名を設定から取得
        let config_file = config.get::<String>("system.active_contest_yaml")
            .unwrap_or_else(|_| "contests.yaml".to_string());
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
        let language = self.language.as_ref()
            .ok_or_else(|| "言語が設定されていません".to_string())?;

        // config/mod.rsを使用して言語設定を取得
        let config = Config::builder()
            .map_err(|e| format!("設定の読み込みに失敗しました: {}", e))?;
        
        // 拡張子を取得
        let extension = config.get::<String>(&format!("{}.extension", language))
            .map_err(|_| format!("未知の言語です: {}", language))?;

        // ファイル名のパターンを取得
        let pattern = config.get::<String>(&format!("system.templates.patterns.{}", file_type))
            .unwrap_or_else(|_| format!("{}.{{extension}}", file_type));
        
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
    }

    // generator.[ext]のパスを取得
    pub fn get_generator_path(&self, problem_id: &str) -> Result<PathBuf> {
        self.get_problem_file_path(problem_id, "generator")
    }

    // tester.[ext]のパスを取得
    pub fn get_tester_path(&self, problem_id: &str) -> Result<PathBuf> {
        self.get_problem_file_path(problem_id, "tester")
    }

    pub fn set_contest(&mut self, contest_id: String) {
        self.contest_id = contest_id;
    }

    pub fn set_language(&mut self, language: &str) -> Result<()> {
        // config/mod.rsを使用して設定を取得
        let config = Config::builder()
            .map_err(|e| format!("設定の読み込みに失敗しました: {}", e))?;

        // エイリアス解決を使用して言語名を取得
        let resolved = config.get_with_alias::<String>(&format!("{}.name", language))
            .map_err(|_| format!("無効な言語です: {}", language))?;

        self.language = Some(resolved);
        Ok(())
    }

    pub fn set_site(&mut self, site_name: &str) -> Result<()> {
        // config/mod.rsを使用して設定を取得
        let config = Config::builder()
            .map_err(|e| format!("設定の読み込みに失敗しました: {}", e))?;

        // エイリアス解決を使用してサイト名を取得
        let resolved = config.get_with_alias::<String>(&format!("{}.name", site_name))
            .map_err(|_| format!("無効なサイトです: {}", site_name))?;

        // 解決されたサイト名を適切なenumに変換
        self.site = match resolved.to_lowercase().as_str() {
            "atcoder" => Site::AtCoder,
            _ => return Err(format!("未対応のサイトです: {}", resolved).into()),
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
        // .moveignoreの読み込み
        let ignore_patterns = self.read_moveignore()?;
        
        // config/mod.rsを使用して設定を取得
        let config = Config::builder()
            .map_err(|e| format!("設定の読み込みに失敗しました: {}", e))?;

        // コンテストの保存先ディレクトリを設定から取得
        let storage_base = config.get::<String>("system.contest_dir.storage")
            .unwrap_or_else(|_| "contests".to_string());
        let contests_dir = self.workspace_dir.join(&storage_base);

        if !contests_dir.exists() {
            fs::create_dir_all(&contests_dir)?;
        }

        // コンテスト用のディレクトリを作成
        let contest_dir = contests_dir.join(&self.contest_id);
        if !contest_dir.exists() {
            fs::create_dir_all(&contest_dir)?;
        }

        // 再帰的にデァイルを探索して移動する関数
        fn move_files(
            source_dir: &Path,
            target_base: &Path,
            relative_path: &Path,
            ignore_patterns: &[String],
            should_ignore: &dyn Fn(&str, &[String]) -> bool
        ) -> Result<bool> {
            let mut has_moved = false;

            for entry in fs::read_dir(source_dir)? {
                let entry = entry?;
                let path = entry.path();
                let name = path.file_name()
                    .ok_or_else(|| format!("Invalid name: {}", path.display()))?
                    .to_string_lossy()
                    .into_owned();

                // .moveignoreパターンに一致する場合はスキップ
                if should_ignore(&name, ignore_patterns) {
                    println!("移動をスキップ: {}", name);
                    continue;
                }

                if path.is_dir() {
                    // ディレクトリの場合は再帰的に処理
                    let new_relative = relative_path.join(&name);
                    if move_files(&path, target_base, &new_relative, ignore_patterns, should_ignore)? {
                        has_moved = true;
                    }
                } else {
                    // ファイルの場合は移動先ディレクトリを作成してから移動
                    let target_dir = target_base.join(relative_path);
                    if !target_dir.exists() {
                        fs::create_dir_all(&target_dir)?;
                    }
                    let target_path = target_dir.join(&name);
                    println!("ファイルを移動: {} -> {}", path.display(), target_path.display());
                    fs::rename(&path, &target_path)?;
                    has_moved = true;
                }
            }

            Ok(has_moved)
        }

        // ルートディレクトリからの相対パスを空のPathBufで初期化
        move_files(
            &self.active_contest_dir,
            &contest_dir,
            &PathBuf::new(),
            &ignore_patterns,
            &|n, p| self.should_ignore(n, p)
        )?;

        Ok(())
    }

    // .moveignoreファイルを読み込む
    fn read_moveignore(&self) -> Result<Vec<String>> {
        // config/mod.rsを使用して設定を取得
        let config = Config::builder()
            .map_err(|e| format!("設定の読み込みに失敗しました: {}", e))?;

        let moveignore_path = self.active_contest_dir.join(".moveignore");
        let mut patterns = vec![];

        // .moveignoreが存在しない場合はデフォルトのパターンを設定から取得
        if !moveignore_path.exists() {
            // コンテスト設定ファイル名を取得
            let config_file = config.get::<String>("system.active_contest_yaml")
                .unwrap_or_else(|_| "contests.yaml".to_string());

            // デフォルトの無視パターンを設定から取得
            let mut default_patterns = vec![config_file];

            // 設定から追加の無視パターンを取得
            if let Ok(additional_patterns) = config.get::<Vec<String>>("system.ignore_patterns") {
                default_patterns.extend(additional_patterns);
            } else {
                default_patterns.push(".moveignore".to_string());
            }

            return Ok(default_patterns);
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

        // config/mod.rsを使用して設定を取得
        let config = Config::builder()
            .map_err(|e| format!("設定の読み込みに失敗しました: {}", e))?;

        // 問題ディレクトリのパスを生成
        let problem_dir = self.active_contest_dir.join(problem_id);
        if !problem_dir.exists() {
            fs::create_dir_all(&problem_dir)?;
        }

        // テストディレクトリ名を設定から取得
        let test_dir_name = config.get::<String>("system.test.dir")
            .unwrap_or_else(|_| "test".to_string());
        let test_dir = problem_dir.join(test_dir_name);
        if !test_dir.exists() {
            fs::create_dir_all(&test_dir)?;
        }

        // テンプレートディレクトリのパターンを設定から取得
        let template_pattern = config.get::<String>("system.templates.directory")
            .unwrap_or_else(|_| "{name}".to_string());
        let template_base = config.get::<String>("system.contest_dir.template")
            .unwrap_or_else(|_| "contest_template".to_string());
        
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