use std::sync::Arc;
use std::time::Duration;
use tokio::time::timeout;
use crate::docker::error::{DockerError, DockerResult};
use crate::docker::runner::command::DockerCommandLayer;

pub struct ContainerIO {
    docker: Arc<DockerCommandLayer>,
    container_id: String,
}

impl ContainerIO {
    pub fn new(docker: Arc<DockerCommandLayer>, container_id: String) -> Self {
        Self {
            docker,
            container_id,
        }
    }

    pub async fn write(&self, input: &str) -> DockerResult<()> {
        let (_, stderr) = self.docker
            .run_container_command(&self.container_id, input)
            .await?;

        if !stderr.is_empty() {
            return Err(DockerError::IO(format!(
                "入力の送信中にエラーが発生しました: {}",
                stderr
            )));
        }

        Ok(())
    }

    pub async fn read_stdout(&self, timeout_duration: Duration) -> DockerResult<String> {
        let args = vec!["logs".to_string(), self.container_id.clone()];
        match timeout(timeout_duration, self.docker.run_command(args)).await {
            Ok(result) => {
                let (stdout, _) = result?;
                Ok(stdout)
            }
            Err(_) => Err(DockerError::IO("標準出力の読み取りがタイムアウトしました".to_string())),
        }
    }

    pub async fn read_stderr(&self, timeout_duration: Duration) -> DockerResult<String> {
        let args = vec!["logs".to_string(), "--stderr".to_string(), self.container_id.clone()];
        match timeout(timeout_duration, self.docker.run_command(args)).await {
            Ok(result) => {
                let (_, stderr) = result?;
                Ok(stderr)
            }
            Err(_) => Err(DockerError::IO("標準エラー出力の読み取りがタイムアウトしました".to_string())),
        }
    }
}