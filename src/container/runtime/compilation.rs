use std::process::Command;
use anyhow::{Result, anyhow};
use async_trait::async_trait;
use crate::message;

/// コンパイラの操作を定義するトレイト
#[async_trait]
pub trait CompilerOperations {
    /// ソースコードをコンパイルします
    ///
    /// # Arguments
    /// * `source_code` - コンパイルするソースコード
    /// * `compile_cmd` - コンパイルコマンド（オプション）
    /// * `env_vars` - 環境変数
    ///
    /// # Errors
    /// * コンパイルに失敗した場合
    async fn compile(
        &mut self,
        source_code: &str,
        compile_cmd: Option<Vec<String>>,
        env_vars: Vec<String>,
    ) -> Result<()>;

    /// コンパイル出力を取得します
    ///
    /// # Returns
    /// * `Result<(String, String)>` - (標準出力, 標準エラー出力)のタプル
    ///
    /// # Errors
    /// * コンパイル出力が利用できない場合
    async fn get_compilation_output(&self) -> Result<(String, String)>;
}

/// コンパイル処理を管理する構造体
///
/// # Fields
/// * `container_id` - コンパイル用コンテナのID（オプション）
/// * `last_output` - 最後のコンパイル出力
#[derive(Debug, Default)]
pub struct Compiler {
    container_id: Option<String>,
    last_output: Option<(String, String)>,
}

impl Compiler {
    /// 新しいCompilerインスタンスを作成します
    ///
    /// # Returns
    /// * `Self` - 新しいCompilerインスタンス
    #[must_use = "この関数は新しいCompilerインスタンスを返します"]
    pub const fn new() -> Self {
        Self {
            container_id: None,
            last_output: None,
        }
    }
}

#[async_trait]
impl CompilerOperations for Compiler {
    async fn compile(
        &mut self,
        _source_code: &str,
        compile_cmd: Option<Vec<String>>,
        env_vars: Vec<String>,
    ) -> Result<()> {
        if self.container_id.is_some() {
            return Err(anyhow!(message::error("build_error", "コンパイルは既に実行されています")));
        }

        let command = compile_cmd.unwrap_or_else(|| vec!["gcc".to_string(), "-o".to_string(), "output".to_string()]);
        let output = Command::new(&command[0])
            .args(&command[1..])
            .envs(env_vars.iter().map(|s| {
                let parts: Vec<&str> = s.split('=').collect();
                (parts[0], parts[1])
            }))
            .output()
            .map_err(|e| anyhow!(message::error("build_error", format!("{e}。コマンド: {command:?}"))))?;

        let stdout = String::from_utf8_lossy(&output.stdout).to_string();
        let stderr = String::from_utf8_lossy(&output.stderr).to_string();
        self.last_output = Some((stdout.clone(), stderr.clone()));

        if !output.status.success() {
            return Err(anyhow!(message::error("build_error", 
                format!("標準エラー出力: {stderr}\n標準出力: {stdout}\n終了コード: {:?}", output.status.code()))));
        }

        Ok(())
    }

    async fn get_compilation_output(&self) -> Result<(String, String)> {
        self.last_output.clone()
            .ok_or_else(|| anyhow!(message::error("build_error", "コンパイル出力が利用できません")))
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::fs;

    #[tokio::test]
    async fn test_compile_success() {
        let mut compiler = Compiler::new();
        let source = "int main() { return 0; }";
        
        // 一時ファイルにソースコードを書き込む
        let temp_dir = std::env::temp_dir();
        let source_path = temp_dir.join("test.c");
        let output_path = temp_dir.join("test");
        fs::write(&source_path, source).unwrap();

        let result = compiler.compile(
            source,
            Some(vec![
                "gcc".to_string(),
                source_path.to_str().unwrap().to_string(),
                "-o".to_string(),
                output_path.to_str().unwrap().to_string(),
            ]),
            vec!["CC=gcc".to_string()],
        ).await;

        // クリーンアップ
        let _ = fs::remove_file(source_path);
        let _ = fs::remove_file(output_path);

        assert!(result.is_ok());
    }

    #[tokio::test]
    async fn test_compile_failure() {
        let mut compiler = Compiler::new();
        let result = compiler.compile(
            "invalid code",
            None,
            vec![],
        ).await;
        assert!(result.is_err());
    }
} 