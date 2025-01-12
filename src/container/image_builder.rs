use std::path::PathBuf;
use anyhow::{Result, anyhow};
use async_trait::async_trait;
use containerd_client as containerd;
use containerd_client::services::v1::images_client::ImagesClient;
use containerd_client::services::v1::content_client::ContentClient;
use containerd_client::services::v1::containers_client::ContainersClient;
use containerd_client::services::v1::tasks_client::TasksClient;
use prost_types::Any;
use std::sync::Arc;
use tokio::sync::Mutex;
use tokio::fs::File;
use tokio::io::AsyncReadExt;
use tokio::time::{sleep, Duration};

#[async_trait]
pub trait ImageBuilder: Send + Sync {
    async fn build_image(&self, tag: &str) -> Result<()>;
}

pub struct OfficialImageBuilder {
    image_name: String,
    images: Arc<Mutex<ImagesClient<tonic::transport::Channel>>>,
    containers: Arc<Mutex<ContainersClient<tonic::transport::Channel>>>,
    tasks: Arc<Mutex<TasksClient<tonic::transport::Channel>>>,
    setup_commands: Vec<String>,
}

impl OfficialImageBuilder {
    /// 新しい公式イメージビルダーを作成します。
    ///
    /// # Arguments
    /// * `image_name` - 公式イメージの名前（例: "python:3.9"）
    /// * `socket_path` - containerdのソケットパス
    /// * `setup_commands` - イメージのセットアップコマンド（例: ["apt-get update", "apt-get install -y gcc"]）
    ///
    /// # Returns
    /// 新しい公式イメージビルダーのインスタンス
    ///
    /// # Errors
    /// * containerdクライアントの初期化に失敗した場合
    pub async fn new(image_name: String, socket_path: &str, setup_commands: Vec<String>) -> Result<Self> {
        let channel = containerd::connect(socket_path).await?;
        Ok(Self {
            image_name,
            images: Arc::new(Mutex::new(ImagesClient::new(channel.clone()))),
            containers: Arc::new(Mutex::new(ContainersClient::new(channel.clone()))),
            tasks: Arc::new(Mutex::new(TasksClient::new(channel))),
            setup_commands,
        })
    }

    /// 一時的なコンテナを作成してコマンドを実行します
    async fn run_setup_commands(&self, container_id: &str) -> Result<()> {
        let mut tasks = self.tasks.lock().await;

        for cmd in &self.setup_commands {
            let args: Vec<&str> = cmd.split_whitespace().collect();
            
            // Execリクエストを作成
            let request = containerd::services::v1::ExecProcessRequest {
                container_id: container_id.to_string(),
                exec_id: uuid::Uuid::new_v4().to_string(),
                terminal: false,
                stdin: vec![],
                stdout: vec![],
                stderr: vec![],
                spec: Some(Any {
                    type_url: "types.containerd.io/opencontainers/runtime-spec/1/Process".to_string(),
                    value: serde_json::to_vec(&serde_json::json!({
                        "args": args,
                        "env": ["PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"],
                        "cwd": "/",
                    }))?,
                }),
            };

            // コマンドを実行
            let response = tasks.exec(request).await?;
            let pid = response.into_inner().pid;

            // コマンドの完了を待機
            let request = containerd::services::v1::WaitRequest {
                container_id: container_id.to_string(),
                exec_id: String::new(),
            };

            let response = tasks.wait(request).await?;
            let exit_status = response.into_inner().exit_status;

            if exit_status != 0 {
                return Err(anyhow!("Command failed with status: {}", exit_status));
            }

            // 短い待機時間を入れて、次のコマンドの実行に備える
            sleep(Duration::from_millis(100)).await;
        }

        Ok(())
    }
}

#[async_trait]
impl ImageBuilder for OfficialImageBuilder {
    async fn build_image(&self, tag: &str) -> Result<()> {
        let mut images = self.images.lock().await;
        let mut containers = self.containers.lock().await;
        
        // イメージをプル
        let request = containerd::services::v1::PullImageRequest {
            image: self.image_name.clone(),
            ..Default::default()
        };

        let response = images.pull(request).await?;
        let image = response.into_inner().image
            .ok_or_else(|| anyhow!("Failed to pull image"))?;

        // セットアップコマンドがある場合、一時的なコンテナを作成して実行
        if !self.setup_commands.is_empty() {
            let container_id = uuid::Uuid::new_v4().to_string();

            // 一時的なコンテナを作成
            let request = containerd::services::v1::CreateContainerRequest {
                container: Some(containerd::services::v1::Container {
                    id: container_id.clone(),
                    image: image.name.clone(),
                    runtime: Some(containerd::services::v1::container::Runtime {
                        name: "io.containerd.runc.v2".to_string(),
                        options: None,
                    }),
                    spec: Some(Any {
                        type_url: "types.containerd.io/opencontainers/runtime-spec/1/Spec".to_string(),
                        value: serde_json::to_vec(&serde_json::json!({
                            "ociVersion": "1.0.2",
                            "process": {
                                "terminal": false,
                                "user": {
                                    "uid": 0,
                                    "gid": 0
                                },
                                "args": ["/bin/sh"],
                                "env": ["PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"],
                                "cwd": "/"
                            },
                            "root": {
                                "path": "rootfs"
                            },
                            "linux": {
                                "namespaces": [
                                    { "type": "pid" },
                                    { "type": "ipc" },
                                    { "type": "uts" },
                                    { "type": "mount" },
                                    { "type": "network" }
                                ]
                            }
                        }))?,
                    }),
                    ..Default::default()
                }),
            };

            containers.create(request).await?;

            // セットアップコマンドを実行
            self.run_setup_commands(&container_id).await?;

            // コンテナを削除
            let request = containerd::services::v1::DeleteContainerRequest {
                id: container_id,
            };

            containers.delete(request).await?;
        }

        // イメージにタグを付ける
        let request = containerd::services::v1::TagImageRequest {
            name: image.name,
            tag: tag.to_string(),
        };

        images.tag(request).await?;
        Ok(())
    }
}

pub struct TarImageBuilder {
    tar_path: PathBuf,
    images: Arc<Mutex<ImagesClient<tonic::transport::Channel>>>,
    content: Arc<Mutex<ContentClient<tonic::transport::Channel>>>,
}

impl TarImageBuilder {
    /// 新しいtarイメージビルダーを作成します。
    ///
    /// # Arguments
    /// * `tar_path` - イメージのtarファイルのパス
    /// * `socket_path` - containerdのソケットパス
    ///
    /// # Returns
    /// 新しいtarイメージビルダーのインスタンス
    ///
    /// # Errors
    /// * containerdクライアントの初期化に失敗した場合
    pub async fn new(tar_path: PathBuf, socket_path: &str) -> Result<Self> {
        let channel = containerd::connect(socket_path).await?;
        Ok(Self {
            tar_path,
            images: Arc::new(Mutex::new(ImagesClient::new(channel.clone()))),
            content: Arc::new(Mutex::new(ContentClient::new(channel))),
        })
    }
}

#[async_trait]
impl ImageBuilder for TarImageBuilder {
    async fn build_image(&self, tag: &str) -> Result<()> {
        // tarファイルを読み込む
        let mut file = File::open(&self.tar_path).await?;
        let mut contents = Vec::new();
        file.read_to_end(&mut contents).await?;

        let mut content_client = self.content.lock().await;
        let mut images_client = self.images.lock().await;

        // イメージをインポート
        let request = containerd::services::v1::ImportRequest {
            ref_name: tag.to_string(),
            data: contents,
            ..Default::default()
        };

        content_client.import(request).await?;
        Ok(())
    }
}

pub struct BuilderConfig {
    pub image_type: String,
    pub source: String,
    pub setup_commands: Vec<String>,
}

impl BuilderConfig {
    /// 新しいビルダー設定を作成します。
    ///
    /// # Arguments
    /// * `image_type` - イメージの種類 ("official" または "tar")
    /// * `source` - イメージのソース（公式イメージ名またはtarファイルのパス）
    /// * `setup_commands` - セットアップコマンド（省略可能）
    ///
    /// # Returns
    /// 新しいビルダー設定のインスタンス
    #[must_use]
    pub fn new(image_type: String, source: String, setup_commands: Vec<String>) -> Self {
        Self {
            image_type,
            source,
            setup_commands,
        }
    }

    /// イメージビルダーを作成します。
    ///
    /// # Arguments
    /// * `socket_path` - containerdのソケットパス
    ///
    /// # Returns
    /// * `Some(Box<dyn ImageBuilder>)` - イメージビルダーのインスタンス
    /// * `None` - イメージビルダーが不要な場合
    ///
    /// # Errors
    /// * containerdクライアントの初期化に失敗した場合
    pub async fn create_builder(&self, socket_path: &str) -> Result<Option<Box<dyn ImageBuilder>>> {
        match self.image_type.as_str() {
            "official" => {
                let builder = OfficialImageBuilder::new(
                    self.source.clone(),
                    socket_path,
                    self.setup_commands.clone(),
                ).await?;
                Ok(Some(Box::new(builder)))
            },
            "tar" => {
                let builder = TarImageBuilder::new(PathBuf::from(&self.source), socket_path).await?;
                Ok(Some(Box::new(builder)))
            },
            _ => Ok(None),
        }
    }
} 