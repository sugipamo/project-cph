use std::process::Command;
use anyhow::{Result, anyhow};

pub struct CompilationManager {
    container_id: Option<String>,
}

impl CompilationManager {
    pub fn new() -> Self {
        Self {
            container_id: None,
        }
    }

    pub fn compile(&mut self, command: &[String]) -> Result<()> {
        if self.container_id.is_some() {
            return Err(anyhow!(
                "コンパイルエラー: コンパイルは既に実行されています。新しいコンパイルを開始する前に、現在のコンパイルを終了してください。"
            ));
        }

        let output = Command::new(&command[0])
            .args(&command[1..])
            .output()
            .map_err(|e| anyhow!(
                "コンパイルエラー: コンパイルの実行に失敗しました: {}。\nコマンド: {:?}",
                e,
                command
            ))?;

        if !output.status.success() {
            let stderr = String::from_utf8_lossy(&output.stderr);
            let stdout = String::from_utf8_lossy(&output.stdout);
            return Err(anyhow!(
                "コンパイルエラー: コンパイルに失敗しました。\n標準エラー出力: {}\n標準出力: {}\n終了コード: {:?}",
                stderr,
                stdout,
                output.status.code()
            ));
        }

        Ok(())
    }

    pub fn get_container_id(&self) -> Result<String> {
        self.container_id
            .clone()
            .ok_or_else(|| anyhow!("コンパイルエラー: コンテナIDが取得できませんでした。"))
    }

    pub fn get_output(&self) -> Result<String> {
        let container_id = self.container_id
            .as_ref()
            .ok_or_else(|| anyhow!(
                "コンパイルエラー: コンパイルが実行されていません。compile()メソッドを先に実行してください。"
            ))?;

        let output = Command::new("docker")
            .args(["logs", container_id])
            .output()
            .map_err(|e| anyhow!(
                "コンパイルエラー: コンパイル出力の取得に失敗しました: {}。\nコンテナID: {}",
                e,
                container_id
            ))?;

        String::from_utf8(output.stdout)
            .map_err(|e| anyhow!("コンパイルエラー: コンパイル出力の解析に失敗しました: {}", e))
    }
} 