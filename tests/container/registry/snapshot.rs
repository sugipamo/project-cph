use anyhow::Result;
use cph::config::Config;
use cph::container::registry::ContainerdBuilder;

#[tokio::test]
async fn test_create_snapshot() -> Result<()> {
    let config = Config::get_default_config()?;
    let builder = ContainerdBuilder::new(config).await?;
    let image = "rust:latest";
    
    // コンテナの作成と起動
    let container_id = builder.create_container(image).await?;
    builder.start_container(&container_id).await?;

    // スナップショットの作成
    let snapshot_name = "test-snapshot";
    builder.create_snapshot(&container_id, snapshot_name).await?;

    // クリーンアップ
    builder.cleanup(&container_id).await?;
    Ok(())
}

#[tokio::test]
async fn test_commit_snapshot() -> Result<()> {
    let config = Config::get_default_config()?;
    let builder = ContainerdBuilder::new(config).await?;
    let image = "rust:latest";
    
    // コンテナの作成と起動
    let container_id = builder.create_container(image).await?;
    builder.start_container(&container_id).await?;

    // スナップショットの作成とコミット
    let snapshot_name = "test-snapshot";
    let tag = "test-image:latest";
    builder.create_snapshot(&container_id, snapshot_name).await?;
    builder.commit_snapshot(snapshot_name, tag).await?;

    // クリーンアップ
    builder.cleanup(&container_id).await?;
    Ok(())
}

#[tokio::test]
async fn test_snapshot_with_changes() -> Result<()> {
    let config = Config::get_default_config()?;
    let builder = ContainerdBuilder::new(config).await?;
    let image = "rust:latest";
    
    // コンテナの作成と起動
    let container_id = builder.create_container(image).await?;
    builder.start_container(&container_id).await?;

    // コンテナ内で変更を加える
    let command = vec!["touch".to_string(), "/test-file".to_string()];
    builder.execute_command(&container_id, &command).await?;

    // スナップショットの作成とコミット
    let snapshot_name = "test-snapshot-with-changes";
    let tag = "test-image-with-changes:latest";
    builder.create_snapshot(&container_id, snapshot_name).await?;
    builder.commit_snapshot(snapshot_name, tag).await?;

    // クリーンアップ
    builder.cleanup(&container_id).await?;
    Ok(())
} 