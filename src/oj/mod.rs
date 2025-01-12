use std::path::PathBuf;
use anyhow::Result;
use colored::Colorize;
use tokio::process::Command;
use containerd_client as containerd;
use containerd_client::services::v1::images_client::ImagesClient;
use containerd_client::services::v1::containers_client::ContainersClient;
use std::sync::Arc;
use tokio::sync::Mutex;

const COOKIE_DIR: &str = ".local/share/online-judge-tools";
const COOKIE_FILE: &str = "cookie.jar";
const CONTAINER_IMAGE_NAME: &str = "oj-container";
const ERROR_CONTAINER_IMAGE_NOT_FOUND: &str = "コンテナイメージが見つかりません。'cargo run -- atcoder login'を実行してログインしてください。";

pub struct OnlineJudge {
    images: Arc<Mutex<ImagesClient<tonic::transport::Channel>>>,
    containers: Arc<Mutex<ContainersClient<tonic::transport::Channel>>>,
}

impl OnlineJudge {
    pub async fn new(socket_path: &str) -> Result<Self> {
        let channel = containerd::connect(socket_path).await?;
        Ok(Self {
            images: Arc::new(Mutex::new(ImagesClient::new(channel.clone()))),
            containers: Arc::new(Mutex::new(ContainersClient::new(channel))),
        })
    }

    async fn run_command(&self, args: &[&str]) -> Result<()> {
        let container_id = uuid::Uuid::new_v4().to_string();
        
        // コンテナを作成
        let request = containerd::services::v1::CreateContainerRequest {
            container: Some(containerd::services::v1::Container {
                id: container_id.clone(),
                image: CONTAINER_IMAGE_NAME.to_string(),
                runtime: Some(containerd::services::v1::container::Runtime {
                    name: "io.containerd.runc.v2".to_string(),
                    options: None,
                }),
                ..Default::default()
            }),
        };

        let mut containers = self.containers.lock().await;
        containers.create(request).await?;

        // コンテナを起動
        let request = containerd::services::v1::StartRequest {
            container_id: container_id.clone(),
            exec_id: String::new(),
        };

        containers.start(request).await?;

        // コンテナを削除
        let request = containerd::services::v1::DeleteContainerRequest {
            id: container_id,
        };

        containers.delete(request).await?;

        Ok(())
    }

    async fn check_image_exists(&self) -> Result<bool> {
        let request = containerd::services::v1::ListImagesRequest::default();
        let response = self.images.lock().await.list(request).await?;
        
        Ok(response.into_inner().images.iter().any(|image| {
            image.name == CONTAINER_IMAGE_NAME
        }))
    }

    pub async fn login(&self, username: &str, password: &str) -> Result<()> {
        if !self.check_image_exists().await? {
            return Err(ERROR_CONTAINER_IMAGE_NOT_FOUND.into());
        }

        self.run_command(&["login", "-u", username, "-p", password, "https://atcoder.jp/"]).await
    }

    pub async fn submit(&self, contest: &str, problem: &str, file: &str) -> Result<()> {
        if !self.check_image_exists().await? {
            return Err(ERROR_CONTAINER_IMAGE_NOT_FOUND.into());
        }

        self.run_command(&["submit", "-w", "0", &format!("https://atcoder.jp/contests/{}/tasks/{}_{}", contest, contest, problem), file]).await
    }

    pub async fn test(&self, contest: &str, problem: &str, file: &str) -> Result<()> {
        if !self.check_image_exists().await? {
            return Err(ERROR_CONTAINER_IMAGE_NOT_FOUND.into());
        }

        self.run_command(&["test", "-c", &format!("python {}", file), &format!("https://atcoder.jp/contests/{}/tasks/{}_{}", contest, contest, problem)]).await
    }

    pub async fn download(&self, contest: &str, problem: &str) -> Result<()> {
        if !self.check_image_exists().await? {
            return Err(ERROR_CONTAINER_IMAGE_NOT_FOUND.into());
        }

        self.run_command(&["download", &format!("https://atcoder.jp/contests/{}/tasks/{}_{}", contest, contest, problem)]).await
    }
} 