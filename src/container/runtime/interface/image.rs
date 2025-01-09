use async_trait::async_trait;
use anyhow::Result;
use chrono::{DateTime, Utc};
use std::path::PathBuf;

pub mod name;

#[derive(Debug, Clone)]
pub struct ImageInfo {
    pub name: String,
    pub tag: String,
    pub id: String,
    pub size: u64,
    pub created_at: DateTime<Utc>,
}

#[derive(Debug, Clone)]
pub struct ImageConfig {
    pub env: Vec<String>,
    pub cmd: Vec<String>,
    pub working_dir: Option<PathBuf>,
    pub entrypoint: Option<Vec<String>>,
}

#[derive(Debug, Clone)]
pub struct LayerInfo {
    pub id: String,
    pub size: u64,
    pub created_at: DateTime<Utc>,
}

#[derive(Debug, Clone)]
pub struct ImageDetails {
    pub config: ImageConfig,
    pub layers: Vec<LayerInfo>,
    pub created_at: DateTime<Utc>,
    pub author: Option<String>,
}

#[async_trait]
pub trait ImageManager: Send + Sync {
    /// イメージをプルします
    async fn pull(&self, image_name: &str) -> Result<()>;

    /// イメージの一覧を取得します
    async fn list(&self) -> Result<Vec<ImageInfo>>;

    /// イメージを削除します
    async fn remove(&self, image_name: &str) -> Result<()>;

    /// イメージの詳細情報を取得します
    async fn inspect(&self, image_name: &str) -> Result<ImageDetails>;

    /// イメージが存在するか確認します
    async fn exists(&self, image_name: &str) -> Result<bool>;

    /// イメージをエクスポートします
    ///
    /// # TODO
    /// - tarアーカイブへのエクスポート
    /// - レイヤーの個別エクスポート
    async fn export(&self, image_name: &str, output_path: &PathBuf) -> Result<()> {
        unimplemented!("エクスポート機能は未実装です")
    }

    /// イメージをインポートします
    ///
    /// # TODO
    /// - tarアーカイブからのインポート
    /// - レイヤーの個別インポート
    async fn import(&self, input_path: &PathBuf) -> Result<String> {
        unimplemented!("インポート機能は未実装です")
    }

    /// イメージをタグ付けします
    ///
    /// # TODO
    /// - マルチタグ対応
    /// - タグの一括更新
    async fn tag(&self, image_name: &str, new_tag: &str) -> Result<()> {
        unimplemented!("タグ付け機能は未実装です")
    }

    /// イメージをビルドします
    ///
    /// # TODO
    /// - Dockerfileからのビルド
    /// - マルチステージビルド
    /// - キャッシュ制御
    async fn build(&self, context_path: &PathBuf, dockerfile: Option<&PathBuf>) -> Result<String> {
        unimplemented!("ビルド機能は未実装です")
    }

    /// イメージを圧縮します
    ///
    /// # TODO
    /// - レイヤーの最適化
    /// - 不要ファイルの削除
    async fn compress(&self, image_name: &str) -> Result<()> {
        unimplemented!("圧縮機能は未実装です")
    }

    /// イメージの脆弱性をスキャンします
    ///
    /// # TODO
    /// - 脆弱性データベースとの連携
    /// - スキャン結果のレポート生成
    async fn scan(&self, image_name: &str) -> Result<()> {
        unimplemented!("脆弱性スキャン機能は未実装です")
    }
} 