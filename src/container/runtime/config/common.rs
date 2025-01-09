use std::path::PathBuf;
use serde::{Serialize, Deserialize};

/// コンテナの基本設定
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ContainerConfig {
    /// コンテナイメージ名
    pub image: String,

    /// 実行するコマンド
    #[serde(default)]
    pub command: Vec<String>,

    /// 作業ディレクトリ
    #[serde(default)]
    pub working_dir: PathBuf,

    /// 環境変数
    #[serde(default)]
    pub env_vars: Vec<String>,

    /// メモリ制限（バイト単位）
    #[serde(default)]
    pub memory_limit: Option<u64>,

    /// CPUの使用制限（CPUの割合、0.0-1.0）
    #[serde(default)]
    pub cpu_limit: Option<f64>,

    /// ネットワーク設定
    #[serde(default)]
    pub network: Option<NetworkConfig>,
}

/// ネットワーク設定
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct NetworkConfig {
    /// ネットワーク名
    pub name: String,

    /// ポートマッピング（ホストポート:コンテナポート）
    #[serde(default)]
    pub port_mappings: Vec<PortMapping>,

    /// DNSサーバー
    #[serde(default)]
    pub dns: Vec<String>,
}

/// ポートマッピング
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PortMapping {
    /// ホスト側のポート
    pub host_port: u16,

    /// コンテナ側のポート
    pub container_port: u16,

    /// プロトコル（tcp/udp）
    #[serde(default = "default_protocol")]
    pub protocol: String,
}

fn default_protocol() -> String {
    "tcp".to_string()
}

impl Default for ContainerConfig {
    fn default() -> Self {
        Self {
            image: String::new(),
            command: Vec::new(),
            working_dir: PathBuf::from("/"),
            env_vars: Vec::new(),
            memory_limit: None,
            cpu_limit: None,
            network: None,
        }
    }
}

impl ContainerConfig {
    /// 新しい設定インスタンスを作成します
    pub fn new(image: impl Into<String>) -> Self {
        Self {
            image: image.into(),
            ..Default::default()
        }
    }

    /// コマンドを設定します
    pub fn with_command(mut self, command: Vec<String>) -> Self {
        self.command = command;
        self
    }

    /// 作業ディレクトリを設定します
    pub fn with_working_dir(mut self, dir: impl Into<PathBuf>) -> Self {
        self.working_dir = dir.into();
        self
    }

    /// 環境変数を設定します
    pub fn with_env_vars(mut self, env_vars: Vec<String>) -> Self {
        self.env_vars = env_vars;
        self
    }

    /// メモリ制限を設定します
    pub fn with_memory_limit(mut self, limit: u64) -> Self {
        self.memory_limit = Some(limit);
        self
    }

    /// CPU制限を設定します
    pub fn with_cpu_limit(mut self, limit: f64) -> Self {
        self.cpu_limit = Some(limit);
        self
    }

    /// ネットワーク設定を追加します
    pub fn with_network(mut self, network: NetworkConfig) -> Self {
        self.network = Some(network);
        self
    }
} 