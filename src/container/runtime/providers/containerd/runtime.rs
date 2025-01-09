use std::path::PathBuf;
use std::process::Command;
use anyhow::{Result, anyhow};
use async_trait::async_trait;
use crate::container::runtime::{
    interface::ContainerRuntime,
    config::provider::containerd::ContainerdConfig,
};

/// Containerd実行環境の実装
pub struct ContainerdRuntime {
    config: ContainerdConfig,
}

impl ContainerdRuntime {
    /// 新しいContainerdRuntime インスタンスを作成します
    pub fn new(config: ContainerdConfig) -> Self {
        Self { config }
    }

    /// Containerdコマンドを実行します
    async fn execute_ctr_command(&self, args: &[&str]) -> Result<(String, String)> {
        let mut command_args = vec!["--namespace", &self.config.namespace];
        command_args.extend(args);

        let output = Command::new("ctr")
            .args(&command_args)
            .output()
            .map_err(|e| anyhow!("Containerdコマンドの実行に失敗: {}", e))?;

        let stdout = String::from_utf8_lossy(&output.stdout).to_string();
        let stderr = String::from_utf8_lossy(&output.stderr).to_string();

        if !output.status.success() {
            return Err(anyhow!("Containerdコマンドがエラーを返しました: {}", stderr));
        }

        Ok((stdout, stderr))
    }

    /// コンテナ作成用の引数を構築します
    fn build_create_args(&self, image: &str, command: &[String], working_dir: &PathBuf, env_vars: &[String]) -> Vec<String> {
        let mut args = vec!["container", "create".to_string()];

        // スナップショッター設定
        args.extend(vec!["--snapshotter".to_string(), self.config.snapshotter.clone()]);

        // ランタイム設定
        args.extend(vec!["--runtime".to_string(), self.config.runtime.clone()]);

        // 基本設定
        args.extend(vec!["--cwd".to_string(), working_dir.to_string_lossy().to_string()]);

        // 環境変数
        for env in env_vars {
            args.extend(vec!["--env".to_string(), env.clone()]);
        }

        // リソース制限
        if let Some(memory) = self.config.base.memory_limit {
            args.extend(vec!["--memory-limit".to_string(), memory.to_string()]);
        }

        // CNI設定
        if let Some(cni) = &self.config.cni {
            args.extend(vec!["--net-host".to_string()]);
            
            if let Some(ip) = &cni.ip_allocation.as_ref().and_then(|a| a.static_ip.as_ref()) {
                args.extend(vec!["--ip".to_string(), ip.clone()]);
            }
        }

        // イメージとコマンド
        args.push(image.to_string());
        args.extend(command.iter().cloned());

        args
    }
}

#[async_trait]
impl ContainerRuntime for ContainerdRuntime {
    async fn create(
        &self,
        image: &str,
        command: &[String],
        working_dir: &PathBuf,
        env_vars: &[String],
    ) -> Result<String> {
        // イメージのプル（存在しない場合）
        let _ = self.execute_ctr_command(&["image", "pull", image]).await;

        let args = self.build_create_args(image, command, working_dir, env_vars);
        let args_str: Vec<&str> = args.iter().map(AsRef::as_ref).collect();
        
        let (stdout, _) = self.execute_ctr_command(&args_str).await?;
        Ok(stdout.trim().to_string())
    }

    async fn start(&self, container_id: &str) -> Result<()> {
        self.execute_ctr_command(&["container", "start", container_id]).await?;
        Ok(())
    }

    async fn stop(&self, container_id: &str) -> Result<()> {
        self.execute_ctr_command(&["container", "stop", container_id]).await?;
        Ok(())
    }

    async fn remove(&self, container_id: &str) -> Result<()> {
        self.execute_ctr_command(&["container", "rm", container_id]).await?;
        Ok(())
    }

    async fn execute(&self, container_id: &str, command: &str) -> Result<(String, String)> {
        self.execute_ctr_command(&["container", "exec", container_id, "sh", "-c", command]).await
    }

    async fn is_running(&self, container_id: &str) -> Result<bool> {
        let (stdout, _) = self.execute_ctr_command(&["container", "info", container_id]).await?;
        Ok(stdout.contains("\"status\": \"running\""))
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::container::runtime::config::common::ContainerConfig;

    #[tokio::test]
    async fn test_build_create_args() {
        let base_config = ContainerConfig::new("docker.io/library/nginx:latest")
            .with_command(vec!["nginx".to_string(), "-g".to_string(), "daemon off;".to_string()])
            .with_working_dir("/app")
            .with_env_vars(vec!["FOO=bar".to_string()]);

        let containerd_config = ContainerdConfig::new(base_config);
        let runtime = ContainerdRuntime::new(containerd_config);

        let args = runtime.build_create_args(
            "docker.io/library/nginx:latest",
            &["nginx".to_string(), "-g".to_string(), "daemon off;".to_string()],
            &PathBuf::from("/app"),
            &["FOO=bar".to_string()],
        );

        assert!(args.contains(&"container".to_string()));
        assert!(args.contains(&"create".to_string()));
        assert!(args.contains(&"--snapshotter".to_string()));
        assert!(args.contains(&"--runtime".to_string()));
        assert!(args.contains(&"--cwd".to_string()));
        assert!(args.contains(&"--env".to_string()));
        assert!(args.contains(&"FOO=bar".to_string()));
    }
} 