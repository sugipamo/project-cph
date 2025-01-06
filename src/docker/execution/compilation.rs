use std::path::Path;
use tokio::process::Command;
use crate::error::Result;
use crate::docker::error::compilation_err;

pub struct CompilationManager {
    container_id: Option<String>,
}

impl CompilationManager {
    pub fn new() -> Self {
        Self {
            container_id: None,
        }
    }

    pub async fn compile<P: AsRef<Path>>(&mut self, _source_code: &str, compile_cmd: Option<Vec<String>>, env_vars: Vec<String>, working_dir: P) -> Result<()> {
        if self.container_id.is_some() {
            return Err(compilation_err(
                "コンパイルは既に実行されています。新しいコンパイルを開始する前に、現在のコンパイルを終了してください。".to_string()
            ));
        }

        let mut command = Command::new("docker");
        command
            .arg("run")
            .arg("--rm")
            .args(env_vars.iter().flat_map(|var| vec!["-e", var]))
            .arg("-w")
            .arg(working_dir.as_ref().to_string_lossy().to_string());

        if let Some(cmd) = compile_cmd {
            command.args(cmd);
        }

        let output = command
            .output()
            .await
            .map_err(|e| compilation_err(format!(
                "コンパイルの実行に失敗しました: {}。\nコマンド: {:?}", 
                e, 
                command
            )))?;

        if !output.status.success() {
            let stderr = String::from_utf8_lossy(&output.stderr);
            let stdout = String::from_utf8_lossy(&output.stdout);
            return Err(compilation_err(format!(
                "コンパイルに失敗しました。\n標準エラー出力: {}\n標準出力: {}\n終了コード: {:?}",
                stderr,
                stdout,
                output.status.code()
            )));
        }

        let container_id = String::from_utf8_lossy(&output.stdout)
            .trim()
            .to_string();
        
        if container_id.is_empty() {
            return Err(compilation_err("コンテナIDが取得できませんでした。".to_string()));
        }

        self.container_id = Some(container_id);
        Ok(())
    }

    pub async fn get_compilation_output(&self) -> Result<(String, String)> {
        let container_id = self.container_id.as_ref()
            .ok_or_else(|| compilation_err(
                "コンパイルが実行されていません。compile()メソッドを先に実行してください。".to_string()
            ))?;

        let output = Command::new("docker")
            .arg("logs")
            .arg(container_id)
            .output()
            .await
            .map_err(|e| compilation_err(format!(
                "コンパイル出力の取得に失敗しました: {}。\nコンテナID: {}", 
                e, 
                container_id
            )))?;

        Ok((
            String::from_utf8_lossy(&output.stdout).to_string(),
            String::from_utf8_lossy(&output.stderr).to_string(),
        ))
    }
} 