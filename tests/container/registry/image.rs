use anyhow::Result;
use cph::config::Config;
use cph::container::registry::{ContainerdBuilder, ImageBuilder};

#[tokio::test]
async fn test_create_containerd_builder() -> Result<()> {
    let config = Config::get_default_config()?;
    let builder = ContainerdBuilder::new(config).await?;
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

    // コンテナの停止とクリーンアップ
    builder.cleanup(&container_id).await?;
    Ok(())
} 