use anyhow::Result;
use crate::cphelper::config::Config;
use cph::container::registry::ContainerdBuilder;
use uuid::Uuid;

#[tokio::test]
async fn test_create_snapshot() -> Result<()> {
    let config = Config::get_default_config()?;
    let builder = ContainerdBuilder::new(config).await?;
    let image = "rust:latest";
    
    // コンテナの作成と起動
    let container_id = builder.create_container(image).await?;
    builder.start_container(&container_id).await?;

    // スナップショットの作成
    let snapshot_name = format!("test-snapshot-{}", Uuid::new_v4());
    builder.create_snapshot(&container_id, &snapshot_name).await?;

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
    let snapshot_name = format!("test-snapshot-{}", Uuid::new_v4());
    let tag = format!("test-image-{}", Uuid::new_v4());
    
    builder.create_snapshot(&container_id, &snapshot_name).await?;
    builder.commit_snapshot(&snapshot_name, &tag).await?;

    // クリーンアップ
    builder.cleanup(&container_id).await?;
    Ok(())
}

#[tokio::test]
async fn test_snapshot_workflow() -> Result<()> {
    let config = Config::get_default_config()?;
    let builder = ContainerdBuilder::new(config).await?;
    let image = "rust:latest";
    
    // コンテナの作成と起動
    let container_id = builder.create_container(image).await?;
    builder.start_container(&container_id).await?;

    // コマンドの実行
    let command = vec!["rustc".to_string(), "--version".to_string()];
    builder.execute_command(&container_id, &command).await?;

    // スナップショットの作成とコミット
    let snapshot_name = format!("test-snapshot-{}", Uuid::new_v4());
    let tag = format!("test-image-{}", Uuid::new_v4());
    
    builder.create_snapshot(&container_id, &snapshot_name).await?;
    builder.commit_snapshot(&snapshot_name, &tag).await?;

    // 新しいコンテナの作成と検証
    let new_container_id = builder.create_container(&tag).await?;
    builder.start_container(&new_container_id).await?;

    // クリーンアップ
    builder.cleanup(&container_id).await?;
    builder.cleanup(&new_container_id).await?;
    Ok(())
} 