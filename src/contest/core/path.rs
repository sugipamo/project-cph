use std::path::{Path, PathBuf};
use std::fs;
use crate::config::Config;
use crate::contest::error::{Result, ContestError};

/// パス解決を担当する構造体
#[derive(Debug)]
pub struct PathResolver {
    /// 基準となるパス
    base_path: PathBuf,
    /// 設定情報
    config: Config,
}

impl PathResolver {
    /// 新しいパスリゾルバを作成
    pub fn new(base_path: PathBuf, config: Config) -> Self {
        Self {
            base_path,
            config,
        }
    }

    /// テンプレートディレクトリのパスを取得
    pub fn get_template_dir(&self, language: &str) -> Result<PathBuf> {
        let template_dir = self.config.get::<String>(&format!("languages.{}.templates.directory", language))
            .map_err(|e| ContestError::Config {
                message: format!("テンプレートディレクトリの設定取得に失敗: {}", e),
                source: None,
            })?;
        
        let template_base = self.config.get::<String>("system.contest_dir.template")
            .map_err(|e| ContestError::Config {
                message: format!("テンプレートディレクトリの設定取得に失敗: {}", e),
                source: None,
            })?;
        
        let template_path = PathBuf::from(template_base).join(template_dir);
        if !template_path.exists() {
            fs::create_dir_all(&template_path)
                .map_err(|e| ContestError::FileSystem {
                    message: "テンプレートディレクトリの作成に失敗".to_string(),
                    source: e,
                    path: template_path.clone(),
                })?;
        }
        
        Ok(template_path)
    }

    /// コンテスト保存用ディレクトリのパスを取得
    pub fn get_contests_dir(&self) -> Result<PathBuf> {
        let storage_base = self.config.get::<String>("system.contest_dir.storage")
            .map_err(|e| ContestError::Config {
                message: format!("コンテスト保存先ディレクトリの設定取得に失敗: {}", e),
                source: None,
            })?;
        Ok(self.get_absolute_contest_dir()?
            .parent()
            .unwrap()
            .join(storage_base))
    }

    /// 問題ファイルのパスを取得
    pub fn get_problem_file_path(&self, problem_id: &str, language: &str, file_type: &str) -> Result<PathBuf> {
        let extension = self.config.get::<String>(&format!("languages.{}.extension", language))
            .map_err(|e| ContestError::Config {
                message: format!("言語{}の拡張子取得に失敗: {}", language, e),
                source: None,
            })?;

        let pattern = self.config.get::<String>(&format!("languages.{}.templates.patterns.{}", language, file_type))
            .map_err(|e| ContestError::Config {
                message: format!("ファイルパターンの取得に失敗: {}", e),
                source: None,
            })?;

        let file_name = pattern.replace("{extension}", &extension);
        Ok(self.get_absolute_contest_dir()?.join(problem_id).join(file_name))
    }

    /// ソリューションファイルのパスを取得
    pub fn get_solution_path(&self, problem_id: &str, language: &str) -> Result<PathBuf> {
        self.get_problem_file_path(problem_id, language, "solution")
    }

    /// ジェネレータファイルのパスを取得
    pub fn get_generator_path(&self, problem_id: &str, language: &str) -> Result<PathBuf> {
        self.get_problem_file_path(problem_id, language, "generator")
    }

    /// テスターファイルのパスを取得
    pub fn get_tester_path(&self, problem_id: &str, language: &str) -> Result<PathBuf> {
        self.get_problem_file_path(problem_id, language, "tester")
    }

    /// テストディレクトリのパスを取得
    pub fn get_test_dir(&self, problem_id: &str) -> Result<PathBuf> {
        let test_dir = self.config.get::<String>("system.test.dir")
            .map_err(|e| ContestError::Config {
                message: format!("テストディレクトリの設定取得に失敗: {}", e),
                source: None,
            })?;
        Ok(self.get_absolute_contest_dir()?.join(problem_id).join(test_dir))
    }

    /// パス解決のためのヘルパーメソッド
    fn get_absolute_contest_dir(&self) -> Result<PathBuf> {
        let current_dir = std::env::current_dir()
            .map_err(|e| ContestError::FileSystem {
                message: "カレントディレクトリの取得に失敗".to_string(),
                source: e,
                path: PathBuf::from("."),
            })?;
        
        if !current_dir.exists() {
            fs::create_dir_all(&current_dir)
                .map_err(|e| ContestError::FileSystem {
                    message: "ディレクトリの作成に失敗".to_string(),
                    source: e,
                    path: current_dir.clone(),
                })?;
        }
        
        let absolute_path = current_dir.join(&self.base_path);
        if !absolute_path.exists() {
            fs::create_dir_all(&absolute_path)
                .map_err(|e| ContestError::FileSystem {
                    message: "ディレクトリの作成に失敗".to_string(),
                    source: e,
                    path: absolute_path.clone(),
                })?;
        }
        
        Ok(absolute_path)
    }

    /// ディレクトリ内容を再帰的にコピー
    pub fn copy_dir_contents(&self, source: &Path, target: &Path) -> Result<()> {
        for entry in fs::read_dir(source)
            .map_err(|e| ContestError::FileSystem {
                message: "ディレクトリの読み取りに失敗".to_string(),
                source: e,
                path: source.to_path_buf(),
            })? {
            let entry = entry.map_err(|e| ContestError::FileSystem {
                message: "ディレクトリエントリの読み取りに失敗".to_string(),
                source: e,
                path: source.to_path_buf(),
            })?;
            let file_type = entry.file_type()
                .map_err(|e| ContestError::FileSystem {
                    message: "ファイルタイプの取得に失敗".to_string(),
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
                        .map_err(|e| ContestError::FileSystem {
                            message: "ディレクトリの作成に失敗".to_string(),
                            source: e,
                            path: target_path.clone(),
                        })?;
                }
                self.copy_dir_contents(&source_path, &target_path)?;
            } else {
                if !target_path.exists() {
                    println!("ファイルをコピー: {} -> {}", source_path.display(), target_path.display());
                    fs::copy(&source_path, &target_path)
                        .map_err(|e| ContestError::FileSystem {
                            message: "ファイルのコピーに失敗".to_string(),
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
} 