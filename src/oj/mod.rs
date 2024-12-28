use crate::error::Result;
use std::path::PathBuf;
use bollard::Docker;
use bollard::container::{Config, CreateContainerOptions, RemoveContainerOptions};
use bollard::image::BuildImageOptions;
use futures::TryStreamExt;
use std::collections::HashMap;
use std::default::Default;

pub struct OJContainer {
    workspace_path: PathBuf,
    docker: Docker,
}

impl OJContainer {
    pub fn new(workspace_path: PathBuf) -> Result<Self> {
        let docker = Docker::connect_with_local_defaults()?;
        Ok(Self { workspace_path, docker })
    }

    pub async fn ensure_image(&self) -> Result<()> {
        let dockerfile_path = PathBuf::from("src/oj/Dockerfile");
        let dockerfile_contents = std::fs::read_to_string(dockerfile_path)?;

        let build_opts = BuildImageOptions {
            dockerfile: "Dockerfile",
            t: "oj-container",
            ..Default::default()
        };

        let mut build_stream = self.docker.build_image(
            build_opts,
            None,
            Some(dockerfile_contents.into())
        );

        while let Some(build_result) = build_stream.try_next().await? {
            // ビルドログの処理が必要な場合はここで行う
            if let Some(error) = build_result.error {
                return Err(error.into());
            }
        }

        Ok(())
    }

    pub async fn download_test_cases(&self, problem_url: &str, test_dir: &PathBuf) -> Result<()> {
        let mut host_config = HashMap::new();
        host_config.insert(
            self.workspace_path.to_string_lossy().to_string(),
            "/workspace"
        );

        let working_dir = format!(
            "/workspace/{}",
            test_dir.strip_prefix(&self.workspace_path)?.display()
        );

        let config = Config {
            image: Some("oj-container"),
            cmd: Some(vec!["oj", "download", problem_url]),
            working_dir: Some(working_dir),
            host_config: Some(bollard::service::HostConfig {
                binds: Some(vec![
                    format!("{}:/workspace", self.workspace_path.display())
                ]),
                ..Default::default()
            }),
            ..Default::default()
        };

        let options = Some(CreateContainerOptions {
            name: "oj-download",
            platform: None,
        });

        let container = self.docker.create_container(options, config).await?;
        self.docker.start_container(&container.id, None).await?;

        let status = self.docker.wait_container(&container.id, None)
            .try_next()
            .await?
            .ok_or("Container exited without status")?;

        // コンテナの削除
        self.docker
            .remove_container(
                &container.id,
                Some(RemoveContainerOptions {
                    force: true,
                    ..Default::default()
                }),
            )
            .await?;

        if status.status_code != 0 {
            return Err("Failed to download test cases".into());
        }

        Ok(())
    }
} 