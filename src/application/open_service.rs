use anyhow::{Context, Result};
use std::path::{Path, PathBuf};
use std::sync::Arc;

use crate::interfaces::file_system::FileSystem;
use crate::interfaces::shell::Shell;

pub struct OpenService {
    file_system: Arc<dyn FileSystem>,
    #[allow(dead_code)]
    shell: Arc<dyn Shell>,
}

impl OpenService {
    pub fn new(file_system: Arc<dyn FileSystem>, shell: Arc<dyn Shell>) -> Self {
        Self {
            file_system,
            shell,
        }
    }

    pub async fn open_problem(&self, name: String, url: Option<String>) -> Result<()> {
        // 1. 問題ディレクトリの作成
        let problem_dir = PathBuf::from(&name);
        self.create_problem_directory(&problem_dir).await?;
        
        // 2. テンプレートファイルの作成
        self.create_template_files(&problem_dir).await?;
        
        // 3. サンプルディレクトリの作成
        self.create_sample_directory(&problem_dir).await?;
        
        // 4. URLが指定されている場合、テストケースのダウンロードを試みる（今後実装）
        if let Some(url) = url {
            eprintln!("注意: テストケースの自動ダウンロードは今後実装予定です。");
            eprintln!("URL: {}", url);
            eprintln!("\n手動でテストケースをダウンロードして、{}/sample/に配置してください。", name);
            eprintln!("ファイル名の形式: 1.in, 1.out, 2.in, 2.out, ...");
        }
        
        println!("✓ 問題 '{}' のディレクトリを作成しました", name);
        println!("✓ テンプレートファイルを作成しました: {}/main.rs", name);
        println!("✓ サンプルディレクトリを作成しました: {}/sample/", name);
        println!("\n次のステップ:");
        println!("  cd {}", name);
        println!("  # main.rsを編集してソリューションを実装");
        println!("  cph test  # テストを実行");
        
        Ok(())
    }
    
    async fn create_problem_directory(&self, path: &Path) -> Result<()> {
        if self.file_system.exists(path).await? {
            return Err(anyhow::anyhow!("問題ディレクトリ '{}' は既に存在します", path.display()));
        }
        
        self.file_system.create_dir(path).await
            .context("問題ディレクトリの作成に失敗しました")?;
        
        Ok(())
    }
    
    async fn create_template_files(&self, problem_dir: &Path) -> Result<()> {
        // Rust用の基本テンプレート
        let template_content = r#"use std::io;

fn main() {
    let mut input = String::new();
    io::stdin().read_line(&mut input).expect("Failed to read line");
    
    // TODO: 問題を解くコードを実装
    
    println!("{}", input.trim());
}
"#;
        
        let main_file = problem_dir.join("main.rs");
        self.file_system.write(&main_file, template_content).await
            .context("テンプレートファイルの作成に失敗しました")?;
        
        Ok(())
    }
    
    async fn create_sample_directory(&self, problem_dir: &Path) -> Result<()> {
        let sample_dir = problem_dir.join("sample");
        self.file_system.create_dir(&sample_dir).await
            .context("サンプルディレクトリの作成に失敗しました")?;
        
        // サンプルテストケースのプレースホルダーを作成
        let sample_in = sample_dir.join("1.in");
        let sample_out = sample_dir.join("1.out");
        
        self.file_system.write(&sample_in, "# ここに入力例を記入\n").await?;
        self.file_system.write(&sample_out, "# ここに期待される出力を記入\n").await?;
        
        Ok(())
    }
}