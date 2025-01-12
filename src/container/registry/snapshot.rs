use anyhow::Result;
use super::image::ContainerdBuilder;

impl ContainerdBuilder {
    pub(crate) async fn create_snapshot(&self, container_id: &str, snapshot_name: &str) -> Result<()> {
        let mut snapshots = self.snapshots.lock().await;
        snapshots
            .prepare(containerd_client::services::v1::PrepareSnapshotRequest {
                snapshotter: "overlayfs".to_string(),
                key: snapshot_name.to_string(),
                parent: container_id.to_string(),
                labels: Default::default(),
            })
            .await?;
        Ok(())
    }

    pub(crate) async fn commit_snapshot(&self, snapshot_name: &str, tag: &str) -> Result<()> {
        let mut images = self.images.lock().await;
        images
            .create(containerd_client::services::v1::CreateImageRequest {
                image: Some(containerd_client::services::v1::Image {
                    name: tag.to_string(),
                    labels: {
                        let mut labels = std::collections::HashMap::new();
                        labels.insert("containerd.io/snapshot/overlayfs".to_string(), snapshot_name.to_string());
                        labels
                    },
                    target: Some(containerd_client::types::Descriptor {
                        media_type: "application/vnd.oci.image.layer.v1.tar+gzip".to_string(),
                        digest: format!("sha256:{}", snapshot_name),
                        size: 0,
                        ..Default::default()
                    }),
                    ..Default::default()
                }),
            })
            .await?;
        Ok(())
    }
} 