use std::path::PathBuf;

/// コンテナの設定を保持する構造体
#[derive(Clone, Debug)]
pub struct Config {
    /// コンテナのID
    pub id: String,
    /// 使用するイメージ
    pub image: String,
    /// 作業ディレクトリ
    pub working_dir: PathBuf,
    /// コマンド引数
    pub args: Vec<String>,
}

impl Config {
    /// 新しい設定を作成します
    #[must_use]
    pub const fn new(id: String, image: String, working_dir: PathBuf, args: Vec<String>) -> Self {
        Self {
            id,
            image,
            working_dir,
            args,
        }
    }
}

#[derive(Clone, Debug)]
pub struct ResourceLimits {
    pub memory_mb: u64,
    pub cpu_count: u32,
    pub timeout_sec: u32,
}

impl Default for ResourceLimits {
    fn default() -> Self {
        Self {
            memory_mb: 512,
            cpu_count: 1,
            timeout_sec: 30,
        }
    }
} 