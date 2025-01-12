use anyhow::Result;
use crate::cphelper::config::Config;
use cph::container::registry::ContainerdBuilder;

#[tokio::test]
async fn test_execute_command() -> Result<()> {
    let config = Config::get_default_config()?;
    let builder = ContainerdBuilder::new(config).await?;
    let image = "rust:latest";
    
    // コンテナの作成と起動
    let container_id = builder.create_container(image).await?;
    builder.start_container(&container_id).await?;

    // コマンドの実行
    let command = vec!["rustc".to_string(), "--version".to_string()];
    let output = builder.execute_command(&container_id, &command).await?;
    
    // 出力の検証
    assert!(!output.stdout.is_empty());
    assert_eq!(output.exit_code, 0);

    // クリーンアップ
    builder.cleanup(&container_id).await?;
    Ok(())
}

#[tokio::test]
async fn test_command_with_env_vars() -> Result<()> {
    let config = Config::get_default_config()?;
    let builder = ContainerdBuilder::new(config).await?;
    let image = "rust:latest";
    
    // コンテナの作成と起動
    let container_id = builder.create_container(image).await?;
    builder.start_container(&container_id).await?;

    // 環境変数を使用するコマンドの実行
    let command = vec!["sh".to_string(), "-c".to_string(), "echo $RUST_BACKTRACE".to_string()];
    let output = builder.execute_command(&container_id, &command).await?;
    
    // 出力の検証
    assert!(!output.stdout.is_empty());
    assert_eq!(output.exit_code, 0);

    // クリーンアップ
    builder.cleanup(&container_id).await?;
    Ok(())
}

#[tokio::test]
async fn test_command_with_error() -> Result<()> {
    let config = Config::get_default_config()?;
    let builder = ContainerdBuilder::new(config).await?;
    let image = "rust:latest";
    
    // コンテナの作成と起動
    let container_id = builder.create_container(image).await?;
    builder.start_container(&container_id).await?;

    // 存在しないコマンドの実行
    let command = vec!["nonexistent_command".to_string()];
    let result = builder.execute_command(&container_id, &command).await;
    
    // エラーの検証
    assert!(result.is_err());

    // クリーンアップ
    builder.cleanup(&container_id).await?;
    Ok(())
} 