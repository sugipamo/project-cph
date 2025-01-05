use std::path::PathBuf;
use crate::contest::error::{Result, ContestError};
use std::fs;

/// テスト関連の機能を提供する構造体
#[derive(Debug)]
pub struct TestManager {
    /// テストディレクトリ
    test_dir: PathBuf,
    /// ジェネレータファイルのパス
    generator_path: PathBuf,
    /// テスターファイルのパス
    tester_path: PathBuf,
    /// 使用言語
    language: String,
}

impl TestManager {
    /// 新しいテストマネージャーを作成
    pub fn new(
        test_dir: PathBuf,
        generator_path: PathBuf,
        tester_path: PathBuf,
        language: String,
    ) -> Result<Self> {
        // テストディレクトリの作成
        if !test_dir.exists() {
            fs::create_dir_all(&test_dir)
                .map_err(|e| ContestError::FileSystem {
                    message: "テストディレクトリの作成に失敗".to_string(),
                    source: e,
                    path: test_dir.clone(),
                })?;
        }

        Ok(Self {
            test_dir,
            generator_path,
            tester_path,
            language,
        })
    }

    /// テストを生成
    pub fn generate(&self) -> Result<()> {
        println!("テストを生成します...");
        println!("言語: {}", self.language);
        println!("テストディレクトリ: {}", self.test_dir.display());
        println!("ジェネレータ: {}", self.generator_path.display());
        println!("テスター: {}", self.tester_path.display());

        // ジェネレータが存在する場合は実行
        if self.generator_path.exists() {
            // TODO: 言語に応じたコンパイルと実行
        }

        Ok(())
    }

    /// テストを実行
    pub fn run(&self, problem_id: &str) -> Result<()> {
        if !self.test_dir.exists() {
            return Err(ContestError::FileSystem {
                message: "テストディレクトリが存在しません".to_string(),
                source: std::io::Error::new(
                    std::io::ErrorKind::NotFound,
                    "test directory not found"
                ),
                path: self.test_dir.clone(),
            });
        }

        // テストケースのファイルを列挙
        let mut test_files = Vec::new();
        for entry in fs::read_dir(&self.test_dir)? {
            let entry = entry?;
            let path = entry.path();
            if path.is_file() && path.extension().map_or(false, |ext| ext == "in") {
                test_files.push(path);
            }
        }

        if test_files.is_empty() {
            return Err(ContestError::Validation {
                message: "テストケースが見つかりません".to_string(),
            });
        }

        println!("問題 {} のテストを実行します...", problem_id);
        println!("言語: {}", self.language);
        println!("テストケース数: {}", test_files.len());

        // 各テストケースを実行
        for test_file in test_files {
            let input = fs::read_to_string(&test_file)?;
            let expected_path = test_file.with_extension("out");
            let expected = fs::read_to_string(&expected_path)?;

            println!("テストケース {}: 実行中...", test_file.display());
            // TODO: 言語に応じたテスト実行
            println!("入力: {}", input);
            println!("期待される出力: {}", expected);
        }

        Ok(())
    }
} 