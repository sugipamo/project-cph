use anyhow::Result;
use crate::cphelper::config::Config;
use cph::container::registry::{ContainerdBuilder, ImageBuilder};

#[tokio::test]
async fn test_builder_creation() -> Result<()> {
    let config = Config::get_default_config()?;
    let builder = ContainerdBuilder::new(config).await?;
    assert!(builder.create_container("rust:latest").await.is_ok());
    Ok(())
}

#[tokio::test]
async fn test_build_image() -> Result<()> {
    let config = Config::get_default_config()?;
    let builder = ContainerdBuilder::new(config).await?;
    let tag = "test-image:latest";
    builder.build_image(tag).await?;
    Ok(())
}

#[tokio::test]
async fn test_create_container() -> Result<()> {
    let config = Config::get_default_config()?;
    let builder = ContainerdBuilder::new(config).await?;
    let image = "rust:latest";
    let container_id = builder.create_container(image).await?;
    assert!(!container_id.is_empty());
    builder.cleanup(&container_id).await?;
    Ok(())
}

#[tokio::test]
async fn test_container_lifecycle() -> Result<()> {
    let config = Config::get_default_config()?;
    let builder = ContainerdBuilder::new(config).await?;
    let image = "rust:latest";

    // コンテナの作成
    let container_id = builder.create_container(image).await?;
    assert!(!container_id.is_empty());

    // コンテナの起動
    builder.start_container(&container_id).await?;

    // コンテナの停止
    builder.stop_container(&container_id).await?;

    // クリーンアップ
    builder.cleanup(&container_id).await?;
    Ok(())
} 