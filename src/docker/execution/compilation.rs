use async_trait::async_trait;
use std::sync::Arc;
use crate::docker::error::{DockerError, DockerResult};
use crate::docker::traits::CompilationOperations;
use super::{DockerCommand, DockerCommandExecutor};

pub struct DefaultCompilationManager {
    docker_executor: Arc<dyn DockerCommandExecutor>,
    container_id: String,
}

impl DefaultCompilationManager {
    pub fn new(executor: Arc<dyn DockerCommandExecutor>, container_id: String) -> Self {
        Self {
            docker_executor: executor,
            container_id,
        }
    }

    async fn execute_in_container(&self, cmd: Vec<String>) -> DockerResult<(String, String)> {
        let command = DockerCommand::new("exec")
            .arg(&self.container_id)
            .args(cmd);

        let output = self.docker_executor.execute(command).await?;
        Ok((output.stdout, output.stderr))
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
                .arg(&self.container_id);

            for env_var in env_vars {
                let parts: Vec<&str> = env_var.split('=').collect();
                if parts.len() == 2 {
                    command = command.env(parts[0], parts[1]);
                }
            }

            command = command.args(cmd);

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
        self.execute_in_container(vec!["cat".to_string(), "compilation.log".to_string()]).await
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::sync::Arc;
    use mockall::predicate::*;
    use crate::docker::test_helpers::MockDockerCommandExecutor;

    #[tokio::test]
    async fn test_compilation() {
        let mut mock_executor = MockDockerCommandExecutor::new();
        mock_executor.expect_execute()
            .returning(|_| {
                Ok(super::super::CommandOutput::new(
                    true,
                    String::new(),
                    String::new(),
                ))
            });

        let executor = Arc::new(mock_executor);
        let mut manager = DefaultCompilationManager::new(
            executor,
            "test_container".to_string(),
        );

        let result = manager.compile(
            "test code",
            Some(vec!["gcc".to_string(), "test.c".to_string()]),
            vec![],
        ).await;
        assert!(result.is_ok());
    }
} 