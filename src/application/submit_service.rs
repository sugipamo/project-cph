use anyhow::{Context, Result};
use std::path::PathBuf;
use std::sync::Arc;

use crate::interfaces::file_system::FileSystem;
use crate::interfaces::shell::Shell;

pub struct SubmitService {
    file_system: Arc<dyn FileSystem>,
    #[allow(dead_code)]
    shell: Arc<dyn Shell>,
}

impl SubmitService {
    pub fn new(file_system: Arc<dyn FileSystem>, shell: Arc<dyn Shell>) -> Self {
        Self {
            file_system,
            shell,
        }
    }

    pub async fn submit_solution(&self, problem: String, file: Option<String>) -> Result<()> {
        // 1. 問題ディレクトリの存在確認
        let problem_dir = PathBuf::from(&problem);
        if !self.file_system.exists(&problem_dir).await? {
            return Err(anyhow::anyhow!(
                "問題ディレクトリ '{}' が見つかりません。'cph open {}' で問題を開いてください。",
                problem,
                problem
            ));
        }
        
        // 2. 提出ファイルの特定
        let submit_file = match file {
            Some(f) => PathBuf::from(f),
            None => problem_dir.join("main.rs"),
        };
        
        if !self.file_system.exists(&submit_file).await? {
            return Err(anyhow::anyhow!(
                "提出ファイル '{}' が見つかりません。",
                submit_file.display()
            ));
        }
        
        // 3. ファイルの内容を確認（基本的な検証）
        let content = self.file_system.read(&submit_file).await
            .context("提出ファイルの読み込みに失敗しました")?;
        
        if content.trim().is_empty() {
            return Err(anyhow::anyhow!("提出ファイルが空です。"));
        }
        
        // 4. サンプルテストケースの存在確認（警告のみ）
        let sample_dir = problem_dir.join("sample");
        if !self.file_system.exists(&sample_dir).await? {
            eprintln!("警告: サンプルディレクトリが見つかりません。");
            eprintln!("テストが実行されていない可能性があります。");
        }
        
        println!("✓ 提出ファイル: {}", submit_file.display());
        println!("✓ ファイルサイズ: {} bytes", content.len());
        println!("✓ 基本的な検証に合格しました");
        
        println!("\n提出前のチェックリスト:");
        println!("  ☐ すべてのテストケースがパスしていることを確認 (cph test)");
        println!("  ☐ 不要なデバッグ出力が含まれていないことを確認");
        println!("  ☐ 制限時間内に実行が完了することを確認");
        
        println!("\n注意: 実際の提出機能は今後実装予定です。");
        println!("現在はブラウザから手動で以下の内容を提出してください:");
        println!("  - ファイル: {}", submit_file.display());
        println!("  - 言語: Rust (または適切な言語を選択)");
        
        Ok(())
    }
}