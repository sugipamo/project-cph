use std::sync::Arc;
use anyhow::{Result, anyhow};
use crate::container::runtime::{
    interface::ContainerRuntime,
    config::{
        common::ContainerConfig,
        provider::{
            docker::DockerConfig,
            containerd::ContainerdConfig,
        },
    },
};
use super::{
    docker::DockerRuntime,
    containerd::ContainerdRuntime,
};

/// コンテナランタイムの種類
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum RuntimeType {
    /// Docker
    Docker,
    /// Containerd
    Containerd,
}

/// ランタイム生成のファクトリー
#[derive(Debug)]
pub struct RuntimeFactory;

impl RuntimeFactory {
    /// 新しいランタイムインスタンスを作成します
    ///
    /// # Arguments
    /// * `runtime_type` - 作成するランタイムの種類
    /// * `config` - 基本設定
    ///
    /// # Returns
    /// * `Result<Arc<dyn ContainerRuntime>>` - ランタイムインスタンス
    ///
    /// # Errors
    /// * 設定が無効な場合
    pub fn create(runtime_type: RuntimeType, config: ContainerConfig) -> Result<Arc<dyn ContainerRuntime>> {
        match runtime_type {
            RuntimeType::Docker => {
                let docker_config = DockerConfig::new(config);
                Ok(Arc::new(DockerRuntime::new(docker_config)))
            }
            RuntimeType::Containerd => {
                let containerd_config = ContainerdConfig::new(config);
                Ok(Arc::new(ContainerdRuntime::new(containerd_config)))
            }
        }
    }

    /// 環境変数からランタイムタイプを判定して作成します
    ///
    /// # Arguments
    /// * `config` - 基本設定
    ///
    /// # Returns
    /// * `Result<Arc<dyn ContainerRuntime>>` - ランタイムインスタンス
    ///
    /// # Errors
    /// * 設定が無効な場合
    /// * 環境変数が設定されていない場合
    pub fn create_from_env(config: ContainerConfig) -> Result<Arc<dyn ContainerRuntime>> {
        let runtime_type = std::env::var("CONTAINER_RUNTIME")
            .map(|v| match v.to_lowercase().as_str() {
                "docker" => Ok(RuntimeType::Docker),
                "containerd" => Ok(RuntimeType::Containerd),
                _ => Err(anyhow!("未知のランタイムタイプ: {}", v)),
            })
            .unwrap_or(Ok(RuntimeType::Docker))?;

        Self::create(runtime_type, config)
    }

    /// 指定されたランタイムタイプで設定を作成します
    ///
    /// # Arguments
    /// * `runtime_type` - ランタイムタイプ
    /// * `config` - 基本設定
    ///
    /// # Returns
    /// * `Result<RuntimeConfig>` - ランタイム固有の設定
    pub fn create_config(runtime_type: RuntimeType, config: ContainerConfig) -> Result<RuntimeConfig> {
        match runtime_type {
            RuntimeType::Docker => Ok(RuntimeConfig::Docker(DockerConfig::new(config))),
            RuntimeType::Containerd => Ok(RuntimeConfig::Containerd(ContainerdConfig::new(config))),
        }
    }

    /// 利用可能なランタイムを検出します
    ///
    /// # Returns
    /// * `Vec<RuntimeType>` - 利用可能なランタイムのリスト
    pub fn detect_available_runtimes() -> Vec<RuntimeType> {
        let mut available = Vec::new();

        // Dockerの検出
        if Command::new("docker").arg("--version").output().is_ok() {
            available.push(RuntimeType::Docker);
        }

        // Containerdの検出
        if Command::new("ctr").arg("--version").output().is_ok() {
            available.push(RuntimeType::Containerd);
        }

        available
    }
}

/// ランタイム固有の設定
#[derive(Debug, Clone)]
pub enum RuntimeConfig {
    /// Docker設定
    Docker(DockerConfig),
    /// Containerd設定
    Containerd(ContainerdConfig),
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::process::Command;

    #[test]
    fn test_create_docker_runtime() {
        let config = ContainerConfig::new("nginx:latest");
        let runtime = RuntimeFactory::create(RuntimeType::Docker, config);
        assert!(runtime.is_ok());
    }

    #[test]
    fn test_create_containerd_runtime() {
        let config = ContainerConfig::new("docker.io/library/nginx:latest");
        let runtime = RuntimeFactory::create(RuntimeType::Containerd, config);
        assert!(runtime.is_ok());
    }

    #[test]
    fn test_create_from_env() {
        std::env::set_var("CONTAINER_RUNTIME", "docker");
        let config = ContainerConfig::new("nginx:latest");
        let runtime = RuntimeFactory::create_from_env(config);
        assert!(runtime.is_ok());
    }

    #[test]
    fn test_detect_available_runtimes() {
        let available = RuntimeFactory::detect_available_runtimes();
        assert!(!available.is_empty(), "少なくとも1つのランタイムが利用可能であるべき");
    }
} 