use serde::{Serialize, Deserialize};
use crate::container::runtime::config::common::ContainerConfig;

/// Containerd固有のコンテナ設定
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ContainerdConfig {
    /// 基本設定
    #[serde(flatten)]
    pub base: ContainerConfig,

    /// 名前空間
    #[serde(default = "default_namespace")]
    pub namespace: String,

    /// スナップショッター
    #[serde(default = "default_snapshotter")]
    pub snapshotter: String,

    /// CNIネットワーク設定
    #[serde(default)]
    pub cni: Option<CniConfig>,

    /// ランタイムハンドラー（例: io.containerd.runc.v2）
    #[serde(default = "default_runtime")]
    pub runtime: String,
}

/// CNIネットワーク設定
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct CniConfig {
    /// ネットワーク名
    pub network_name: String,

    /// インターフェース名
    #[serde(default = "default_interface")]
    pub interface: String,

    /// IPアドレス割り当て方式
    #[serde(default)]
    pub ip_allocation: Option<IpAllocation>,
}

/// IPアドレス割り当て設定
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct IpAllocation {
    /// 固定IPアドレス
    pub static_ip: Option<String>,

    /// サブネット
    pub subnet: Option<String>,

    /// ゲートウェイ
    pub gateway: Option<String>,
}

fn default_namespace() -> String {
    "default".to_string()
}

fn default_snapshotter() -> String {
    "overlayfs".to_string()
}

fn default_runtime() -> String {
    "io.containerd.runc.v2".to_string()
}

fn default_interface() -> String {
    "eth0".to_string()
}

impl ContainerdConfig {
    /// 新しいContainerd設定インスタンスを作成します
    pub fn new(base: ContainerConfig) -> Self {
        Self {
            base,
            namespace: default_namespace(),
            snapshotter: default_snapshotter(),
            cni: None,
            runtime: default_runtime(),
        }
    }

    /// 名前空間を設定します
    pub fn with_namespace(mut self, namespace: impl Into<String>) -> Self {
        self.namespace = namespace.into();
        self
    }

    /// スナップショッターを設定します
    pub fn with_snapshotter(mut self, snapshotter: impl Into<String>) -> Self {
        self.snapshotter = snapshotter.into();
        self
    }

    /// CNI設定を追加します
    pub fn with_cni(mut self, cni: CniConfig) -> Self {
        self.cni = Some(cni);
        self
    }

    /// ランタイムを設定します
    pub fn with_runtime(mut self, runtime: impl Into<String>) -> Self {
        self.runtime = runtime.into();
        self
    }
} 