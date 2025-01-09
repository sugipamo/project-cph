use std::path::PathBuf;
use std::process::Command;
use anyhow::{Result, anyhow};
use async_trait::async_trait;
use crate::container::runtime::{
    interface::ContainerRuntime,
    config::provider::docker::DockerConfig,
};

/// Docker実行環境の実装
pub struct DockerRuntime {
    config: DockerConfig,
}

impl DockerRuntime {
    /// 新しいDockerRuntime インスタンスを作成します
    pub fn new(config: DockerConfig) -> Self {
        Self { config }
    }

    /// Dockerコマンドを実行します
    async fn execute_docker_command(&self, args: &[&str]) -> Result<(String, String)> {
        let output = Command::new("docker")
            .args(args)
            .output()
            .map_err(|e| anyhow!("Dockerコマンドの実行に失敗: {}", e))?;

        let stdout = String::from_utf8_lossy(&output.stdout).to_string();
        let stderr = String::from_utf8_lossy(&output.stderr).to_string();

        if !output.status.success() {
            return Err(anyhow!("Dockerコマンドがエラーを返しました: {}", stderr));
        }

        Ok((stdout, stderr))
    }

    /// コンテナ作成用の引数を構築します
    fn build_create_args(&self, image: &str, command: &[String], working_dir: &PathBuf, env_vars: &[String]) -> Vec<String> {
        let mut args = vec!["create".to_string()];

        // 基本設定
        args.push("--workdir".to_string());
        args.push(working_dir.to_string_lossy().to_string());

        // 環境変数
        for env in env_vars {
            args.push("--env".to_string());
            args.push(env.clone());
        }

        // リソース制限
        if let Some(memory) = self.config.base.memory_limit {
            args.push("--memory".to_string());
            args.push(memory.to_string());
        }

        if let Some(cpu) = self.config.base.cpu_limit {
            args.push("--cpus".to_string());
            args.push(cpu.to_string());
        }

        // Docker固有の設定
        if self.config.privileged {
            args.push("--privileged".to_string());
        }

        // ボリューム
        for volume in &self.config.volumes {
            args.push("-v".to_string());
            let mount_opt = if volume.readonly { "ro" } else { "rw" };
            args.push(format!("{}:{}:{}", volume.host_path, volume.container_path, mount_opt));
        }

        // ネットワーク設定
        if let Some(network) = &self.config.base.network {
            args.push("--network".to_string());
            args.push(network.name.clone());

            // ポートマッピング
            for port in &network.port_mappings {
                args.push("-p".to_string());
                args.push(format!("{}:{}/{}", port.host_port, port.container_port, port.protocol));
            }

            // DNS設定
            for dns in &network.dns {
                args.push("--dns".to_string());
                args.push(dns.clone());
            }
        }

        // イメージとコマンド
        args.push(image.to_string());
        args.extend(command.iter().cloned());

        args
    }
}

#[async_trait]
impl ContainerRuntime for DockerRuntime {
    async fn create(
        &self,
        image: &str,
        command: &[String],
        working_dir: &PathBuf,
        env_vars: &[String],
    ) -> Result<String> {
        let args = self.build_create_args(image, command, working_dir, env_vars);
        let args_str: Vec<&str> = args.iter().map(AsRef::as_ref).collect();
        
        let (stdout, _) = self.execute_docker_command(&args_str).await?;
        Ok(stdout.trim().to_string())
    }

    async fn start(&self, container_id: &str) -> Result<()> {
        self.execute_docker_command(&["start", container_id]).await?;
        Ok(())
    }

    async fn stop(&self, container_id: &str) -> Result<()> {
        self.execute_docker_command(&["stop", container_id]).await?;
        Ok(())
    }

    async fn remove(&self, container_id: &str) -> Result<()> {
        self.execute_docker_command(&["rm", "-f", container_id]).await?;
        Ok(())
    }

    async fn execute(&self, container_id: &str, command: &str) -> Result<(String, String)> {
        self.execute_docker_command(&["exec", container_id, "sh", "-c", command]).await
    }

    async fn is_running(&self, container_id: &str) -> Result<bool> {
        let (stdout, _) = self.execute_docker_command(&["inspect", "--format={{.State.Running}}", container_id]).await?;
        Ok(stdout.trim() == "true")
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::container::runtime::config::common::ContainerConfig;

    #[tokio::test]
    async fn test_build_create_args() {
        let base_config = ContainerConfig::new("nginx:latest")
            .with_command(vec!["nginx".to_string(), "-g".to_string(), "daemon off;".to_string()])
            .with_working_dir("/app")
            .with_env_vars(vec!["FOO=bar".to_string()]);

        let docker_config = DockerConfig::new(base_config);
        let runtime = DockerRuntime::new(docker_config);

        let args = runtime.build_create_args(
            "nginx:latest",
            &["nginx".to_string(), "-g".to_string(), "daemon off;".to_string()],
            &PathBuf::from("/app"),
            &["FOO=bar".to_string()],
        );

        assert!(args.contains(&"create".to_string()));
        assert!(args.contains(&"--workdir".to_string()));
        assert!(args.contains(&"/app".to_string()));
        assert!(args.contains(&"--env".to_string()));
        assert!(args.contains(&"FOO=bar".to_string()));
        assert!(args.contains(&"nginx:latest".to_string()));
    }
} 