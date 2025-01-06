use std::process::Stdio;
use tokio::process::Command;
use crate::docker::error::{DockerError, DockerResult};
use std::time::Duration;
use tokio::time::timeout;

#[async_trait::async_trait]
pub trait DockerCommandExecutor {
    async fn check_image(&self, image: &str) -> DockerResult<bool>;
    async fn pull_image(&self, image: &str) -> DockerResult<bool>;
    async fn run_container(
        &self,
        container_name: &str,
        image: &str,
        memory_limit: u32,
        mount_source: &str,
        mount_target: &str,
        command: &str,
        timeout_seconds: u32,
    ) -> DockerResult<String>;
    async fn stop_container(&self, container_name: &str) -> DockerResult<()>;
    async fn inspect_directory(
        &self,
        container_name: &str,
        image: &str,
        mount_point: &str,
    ) -> DockerResult<String>;
}

pub struct DefaultDockerExecutor;

impl DefaultDockerExecutor {
    pub fn new() -> Self {
        Self
    }
}

#[async_trait::async_trait]
impl DockerCommandExecutor for DefaultDockerExecutor {
    async fn check_image(&self, image: &str) -> DockerResult<bool> {
        let output = Command::new("docker")
            .arg("image")
            .arg("inspect")
            .arg(image)
            .stdout(Stdio::null())
            .stderr(Stdio::null())
            .status()
            .await
            .map_err(|e| DockerError::Runtime(format!("イメージの確認に失敗しました: {}", e)))?;

        Ok(output.success())
    }

    async fn pull_image(&self, image: &str) -> DockerResult<bool> {
        let output = Command::new("docker")
            .arg("pull")
            .arg(image)
            .status()
            .await
            .map_err(|e| DockerError::Runtime(format!("イメージの取得に失敗しました: {}", e)))?;

        Ok(output.success())
    }

    async fn run_container(
        &self,
        container_name: &str,
        image: &str,
        memory_limit: u32,
        mount_source: &str,
        mount_target: &str,
        command: &str,
        timeout_seconds: u32,
    ) -> DockerResult<String> {
        let mut cmd = Command::new("docker");
        cmd.arg("run")
            .arg("--rm")
            .arg("--name")
            .arg(container_name)
            .arg("--memory")
            .arg(format!("{}m", memory_limit))
            .arg("--cpus")
            .arg("1.0")
            .arg("--network")
            .arg("none")
            .arg("-v")
            .arg(format!("{}:{}", mount_source, mount_target))
            .arg("-w")
            .arg(mount_target)
            .arg(image)
            .arg("sh")
            .arg("-c")
            .arg(command);

        let timeout_duration = Duration::from_secs(timeout_seconds as u64);
        let output = match timeout(timeout_duration, cmd.output()).await {
            Ok(result) => result.map_err(|e| DockerError::Runtime(format!("コンテナの実行に失敗しました: {}", e)))?,
            Err(_) => {
                self.stop_container(container_name).await?;
                return Err(DockerError::Timeout("実行がタイムアウトしました".to_string()));
            }
        };

        if !output.status.success() {
            return Err(DockerError::Runtime(
                String::from_utf8_lossy(&output.stderr).to_string()
            ));
        }

        Ok(String::from_utf8_lossy(&output.stdout).to_string())
    }

    async fn stop_container(&self, container_name: &str) -> DockerResult<()> {
        Command::new("docker")
            .arg("stop")
            .arg(container_name)
            .output()
            .await
            .map_err(|e| DockerError::Runtime(format!("コンテナの停止に失敗しました: {}", e)))?;

        Ok(())
    }

    async fn inspect_directory(
        &self,
        container_name: &str,
        image: &str,
        mount_point: &str,
    ) -> DockerResult<String> {
        let output = Command::new("docker")
            .arg("run")
            .arg("--rm")
            .arg("--name")
            .arg(container_name)
            .arg(image)
            .arg("ls")
            .arg("-la")
            .arg(mount_point)
            .output()
            .await
            .map_err(|e| DockerError::Runtime(format!("ディレクトリの検査に失敗しました: {}", e)))?;

        Ok(String::from_utf8_lossy(&output.stdout).to_string())
    }
}

#[cfg(test)]
pub struct MockDockerExecutor {
    pub should_fail: bool,
}

#[cfg(test)]
impl MockDockerExecutor {
    pub fn new(should_fail: bool) -> Self {
        Self { should_fail }
    }
}

#[cfg(test)]
#[async_trait::async_trait]
impl DockerCommandExecutor for MockDockerExecutor {
    async fn check_image(&self, _image: &str) -> DockerResult<bool> {
        Ok(true)
    }

    async fn pull_image(&self, _image: &str) -> DockerResult<bool> {
        Ok(true)
    }

    async fn run_container(
        &self,
        _container_name: &str,
        _image: &str,
        _memory_limit: u32,
        _mount_source: &str,
        _mount_target: &str,
        command: &str,
        _timeout_seconds: u32,
    ) -> DockerResult<String> {
        if self.should_fail {
            Err(DockerError::Runtime("モックエラー".to_string()))
        } else {
            if command.contains("main.rs") {
                Ok("Hello from Rust!\n".to_string())
            } else if command.contains("main.py") {
                Ok("Hello from Python!\n".to_string())
            } else if command.contains("main.cpp") {
                Ok("Hello from C++!\n".to_string())
            } else {
                Ok("実行成功\n".to_string())
            }
        }
    }

    async fn stop_container(&self, _container_name: &str) -> DockerResult<()> {
        Ok(())
    }

    async fn inspect_directory(
        &self,
        _container_name: &str,
        _image: &str,
        _mount_point: &str,
    ) -> DockerResult<String> {
        Ok("total 4\ndrwxr-xr-x 2 root root 4096 Jan 1 00:00 .\n".to_string())
    }
} 