use anyhow::Result;
use super::image::ContainerdBuilder;
use containerd_client::services::v1::snapshots::PrepareSnapshotRequest;
use containerd_client::services::v1::CreateImageRequest;
use containerd_client::types::Descriptor;
use std::time::SystemTime;

impl ContainerdBuilder {
    pub(crate) async fn create_snapshot(&self, container_id: &str, snapshot_name: &str) -> Result<()> {
        let mut snapshots = self.snapshots.lock().await;
        snapshots
            .prepare(PrepareSnapshotRequest {
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
        let now = SystemTime::now();
        images
            .create(CreateImageRequest {
                image: Some(containerd_client::services::v1::Image {
                    name: tag.to_string(),
                    target: Some(Descriptor {
                        media_type: "application/vnd.oci.image.manifest.v1+json".to_string(),
                        digest: format!("sha256:{}", snapshot_name),
                        size: 0,
                        annotations: Default::default(),
                    }),
                    created_at: Some(prost_types::Timestamp::from(now)),
                    updated_at: Some(prost_types::Timestamp::from(now)),
                    labels: Default::default(),
                }),
                source_date_epoch: Some(prost_types::Timestamp::from(now)),
            })
            .await?;
        Ok(())
    }
} 