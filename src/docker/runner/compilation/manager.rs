use async_trait::async_trait;
use std::sync::Arc;
use crate::docker::error::{DockerError, DockerResult};
use crate::docker::traits::CompilationOperations;
use crate::docker::executor::{DockerCommand, DockerCommandExecutor};

pub struct DefaultCompilationManager {
    container_id: String,
    docker_executor: Arc<dyn DockerCommandExecutor>,
}

impl DefaultCompilationManager {
    pub fn new(container_id: String, _working_dir: String, executor: Arc<dyn DockerCommandExecutor>) -> Self {
        Self {
            container_id,
            docker_executor: executor,
        }
    }
}

#[async_trait]
impl CompilationOperations for DefaultCompilationManager {
    async fn compile(
        &mut self,
        _source_code: &str,
        compile_cmd: Option<Vec<String>>,
        env_vars: Vec<String>,
    ) -> DockerResult<()> {
        if let Some(cmd) = compile_cmd {
            let mut command = DockerCommand::new("exec")
                .arg("-i")
                .arg(&self.container_id)
                .args(cmd);

            // 環境変数の設定
            for env_var in env_vars {
                let parts: Vec<&str> = env_var.split('=').collect();
                if parts.len() == 2 {
                    command = command.env(parts[0], parts[1]);
                }
            }

            let output = self.docker_executor.execute(command).await?;

            if !output.success {
                return Err(DockerError::Compilation(format!(
                    "コンパイルに失敗しました: {}",
                    output.stderr
                )));
            }
        }
        Ok(())
    }

    async fn get_compilation_output(&self) -> DockerResult<(String, String)> {
        Ok(("".to_string(), "".to_string()))
    }
} 