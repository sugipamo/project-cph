use crate::{cli::Site, error::Result, config::languages::LanguageConfig};
use serde::{Serialize, Deserialize};
use std::path::{PathBuf, Path};
use std::fs;
use std::io::BufRead;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Contest {
    #[serde(default)]
    pub root: PathBuf,
    pub contest_id: String,
    pub language: Option<String>,
    pub site: Site,
}

impl Default for Contest {
    fn default() -> Self {
        Self {
            root: PathBuf::from("active_contest"),
            contest_id: String::new(),
            language: None,
            site: Site::AtCoder,
        }
    }
}

impl Contest {
    pub fn new(_current_dir: PathBuf) -> Result<Self> {
        // active_contestディレクトリを作成
        let active_dir = PathBuf::from("active_contest");
        if !active_dir.exists() {
            println!("active_contestディレクトリを作成します");
            fs::create_dir_all(&active_dir)
                .map_err(|e| format!("active_contestディレクトリの作成に失敗しました: {}", e))?;
        }

        let config_path = active_dir.join("contests.yaml");
        if !config_path.exists() {
            // デフォルトのコンテスト設定を作成し、デフォルト言語を設定
            let mut contest = Self::default();
            contest.root = active_dir;

            // 言語設定からデフォルト言語を取得
            if let Ok(lang_config) = LanguageConfig::load(PathBuf::from("src/config/languages.yaml")) {
                if let Some(default_lang) = lang_config.get_default_language() {
                    contest.language = Some(default_lang);
                }
            }

            return Ok(contest);
        }

        let content = fs::read_to_string(&config_path)?;
        let mut contest: Contest = serde_yaml::from_str(&content)
            .map_err(|e| format!("contests.yamlの解析に失敗しました: {}", e))?;
        
        // rootを相対パスに設定
        contest.root = active_dir;

        Ok(contest)
    }

    pub fn save(&self) -> Result<()> {
        let config_path = self.root.join("contests.yaml");
        let content = serde_yaml::to_string(&self)
            .map_err(|e| format!("Failed to serialize contest config: {}", e))?;
        fs::write(config_path, content)?;

        // テンプレートファイルのコピー
        self.copy_template()?;

        // 既存のファイルを移動
        self.move_files_to_contests()?;

        Ok(())
    }

    pub fn get_source_path(&self, problem_id: &str) -> Result<PathBuf> {
        let language = self.language.as_ref()
            .ok_or_else(|| "言語が設定されていません".to_string())?;

        // 言語設定を読み込む
        let lang_config = LanguageConfig::load(PathBuf::from("src/config/languages.yaml"))?;
        
        // 拡張子を取得
        let extension = lang_config.get_extension(language)
            .ok_or_else(|| format!("未知の言語です: {}", language))?;

        Ok(self.root.join(format!("{}.{}", problem_id, extension)))
    }

    pub fn set_contest(&mut self, contest_id: String) {
        self.contest_id = contest_id;
    }

    pub fn set_language(&mut self, language: &str) {
        self.language = Some(language.to_lowercase());
    }

    pub fn set_site(&mut self, site: Site) {
        self.site = site;
    }

    // テンプレートファイルのコピー
    fn copy_template(&self) -> Result<()> {
        if let Some(language) = &self.language {
            // 言語設定を読み込む
            let lang_config = LanguageConfig::load(PathBuf::from("src/config/languages.yaml"))?;
            
            // テンプレートパスを取得
            if let Some(template_path) = lang_config.get_template(language, "solution") {
                let source = PathBuf::from("templates/template").join(&template_path.solution);
                if !source.exists() {
                    return Err(format!("テンプレートファイルが見つかりません: {}", source.display()).into());
                }

                // テンプレートディレクトリをコピー
                let target = self.root.join("template");
                if !target.exists() {
                    println!("テンプレートディレクトリを作成: {}", target.display());
                    fs::create_dir_all(&target)?;
                }

                println!("テンプレートをコピーしています...");
                println!("From: {}", source.display());
                println!("To: {}", target.display());

                // ファイルをコピー
                fs::copy(&source, target.join(&template_path.solution))?;
                println!("テンプレートのコピーが完了しました");
            }
        }
        Ok(())
    }

    // ディレクトリ内容のコピー（再帰的）
    #[allow(dead_code)]
    fn copy_dir_contents(&self, source: &Path, target: &Path) -> Result<()> {
        for entry in fs::read_dir(source)? {
            let entry = entry?;
            let file_type = entry.file_type()?;
            let source_path = entry.path();
            let file_name = entry.file_name();
            let target_path = target.join(&file_name);

            if file_type.is_dir() {
                // ディレクトリの場合は再帰的にコピー
                if !target_path.exists() {
                    println!("ディレクトリを作成: {}", target_path.display());
                    fs::create_dir_all(&target_path)?;
                }
                self.copy_dir_contents(&source_path, &target_path)?;
            } else {
                // ファイルの場合は、存在しない場合のみコピー
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
        
        // contestsディレクトリの作成
        let contests_dir = PathBuf::from("contests");
        if !contests_dir.exists() {
            fs::create_dir_all(&contests_dir)?;
        }

        // コンテスト用のディレクトリを作成
        let contest_dir = contests_dir.join(&self.contest_id);
        if !contest_dir.exists() {
            fs::create_dir_all(&contest_dir)?;
        }

        // ファイルの移動
        for entry in fs::read_dir(&self.root)? {
            let entry = entry?;
            let path = entry.path();
            let file_name = path.file_name()
                .ok_or_else(|| format!("Invalid file name: {}", path.display()))?
                .to_string_lossy()
                .into_owned();

            // .moveignoreパターンに一致するファイルはスキップ
            if self.should_ignore(&file_name, &ignore_patterns) {
                println!("移動をスキップ: {}", file_name);
                continue;
            }

            // ファイルを移動
            if path.is_file() {
                let target_path = contest_dir.join(&file_name);
                println!("ファイルを移動: {} -> {}", path.display(), target_path.display());
                fs::rename(&path, &target_path)?;
            }
        }

        Ok(())
    }

    // .moveignoreファイルを読み込む
    fn read_moveignore(&self) -> Result<Vec<String>> {
        let moveignore_path = self.root.join(".moveignore");
        let mut patterns = vec![];

        // .moveignoreが存在しない場合はデフォルトのパターンを返す
        if !moveignore_path.exists() {
            return Ok(vec![
                "template".to_string(),
                "template/**".to_string(),
                "contests.yaml".to_string(),
                ".moveignore".to_string(),
            ]);
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
} 