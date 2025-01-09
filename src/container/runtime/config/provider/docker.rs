use std::collections::HashMap;
use serde::{Serialize, Deserialize};
use crate::container::runtime::config::common::ContainerConfig;

/// Docker固有のコンテナ設定
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct DockerConfig {
    /// 基本設定
    #[serde(flatten)]
    pub base: ContainerConfig,

    /// 特権モード
    #[serde(default)]
    pub privileged: bool,

    /// ボリュームマウント
    #[serde(default)]
    pub volumes: Vec<VolumeMount>,

    /// 追加のホスト設定
    #[serde(default)]
    pub extra_hosts: HashMap<String, String>,

    /// カスタムラベル
    #[serde(default)]
    pub labels: HashMap<String, String>,

    /// リスタートポリシー
    #[serde(default)]
    pub restart_policy: Option<RestartPolicy>,
}

/// ボリュームマウント設定
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct VolumeMount {
    /// ホスト側のパス
    pub host_path: String,

    /// コンテナ側のパス
    pub container_path: String,

    /// 読み取り専用かどうか
    #[serde(default)]
    pub readonly: bool,
}

/// リスタートポリシー
#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(rename_all = "lowercase")]
pub enum RestartPolicy {
    /// リスタートしない
    No,
    /// 常にリスタート
    Always,
    /// 異常終了時のみリスタート
    OnFailure,
    /// 特定の条件でリスタート
    UnlessStopped,
}

impl DockerConfig {
    /// 新しいDocker設定インスタンスを作成します
    pub fn new(base: ContainerConfig) -> Self {
        Self {
            base,
            privileged: false,
            volumes: Vec::new(),
            extra_hosts: HashMap::new(),
            labels: HashMap::new(),
            restart_policy: None,
        }
    }

    /// 特権モードを設定します
    pub fn with_privileged(mut self, privileged: bool) -> Self {
        self.privileged = privileged;
        self
    }

    /// ボリュームマウントを追加します
    pub fn with_volume(mut self, volume: VolumeMount) -> Self {
        self.volumes.push(volume);
        self
    }

    /// 追加のホスト設定を追加します
    pub fn with_extra_host(mut self, hostname: impl Into<String>, ip: impl Into<String>) -> Self {
        self.extra_hosts.insert(hostname.into(), ip.into());
        self
    }

    /// ラベルを追加します
    pub fn with_label(mut self, key: impl Into<String>, value: impl Into<String>) -> Self {
        self.labels.insert(key.into(), value.into());
        self
    }

    /// リスタートポリシーを設定します
    pub fn with_restart_policy(mut self, policy: RestartPolicy) -> Self {
        self.restart_policy = Some(policy);
        self
    }
} 