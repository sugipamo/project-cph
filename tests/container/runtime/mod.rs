mod mock;

#[cfg(test)]
mod tests {
    use super::mock::MockRuntime;
    use cph::container::{
        runtime::Container,
        runtime::config::Config,
        communication::Network,
        io::Buffer,
        state::lifecycle::Status,
    };
    use std::{path::PathBuf, sync::Arc};
    use anyhow::Result;
    use tokio::time::{sleep, Duration};

    async fn setup_test_container() -> Result<Container> {
        let config = Config::new(
            "test-container".to_string(),
            "rust:latest".to_string(),
            PathBuf::from("/workspace"),
            vec!["sleep".to_string(), "1".to_string()],
        );
        let network = Arc::new(Network::new());
        let buffer = Arc::new(Buffer::new());
        let runtime = MockRuntime::new("test-container".to_string());
        Container::with_runtime(config, network, buffer, runtime).await
    }

    async fn setup_language_container(
        language: &str,
        source_file: &str,
        args: Vec<String>
    ) -> Result<Container> {
        let config = Config::new(
            format!("test-{}-container", language),
            format!("{}:latest", language),
            PathBuf::from("/workspace").join(source_file).parent().unwrap_or(&PathBuf::from("/workspace")).to_path_buf(),
            args,
        );
        let network = Arc::new(Network::new());
        let buffer = Arc::new(Buffer::new());
        let runtime = MockRuntime::new(format!("test-{}-container", language));
        Container::with_runtime(config, network, buffer, runtime).await
    }

    #[tokio::test]
    async fn test_container_lifecycle() -> Result<()> {
        let container = setup_test_container().await?;
        
        // 初期状態の確認
        assert_eq!(container.status().await, Status::Created);

        // コンテナの実行
        let handle = tokio::spawn({
            let container = container.clone();
            async move {
                container.run().await
            }
        });

        // 少し待ってステータスを確認
        sleep(Duration::from_millis(100)).await;
        assert_eq!(container.status().await, Status::Running);
        
        // クリーンアップ
        container.cleanup().await?;
        assert_eq!(container.status().await, Status::Stopped);
        
        // 実行完了を待つ
        handle.abort();
        
        Ok(())
    }

    #[tokio::test]
    async fn test_container_cleanup() -> Result<()> {
        let container = setup_test_container().await?;
        
        // コンテナを実行状態にする
        let handle = tokio::spawn({
            let container = container.clone();
            async move {
                container.run().await
            }
        });

        // 少し待ってからクリーンアップ
        sleep(Duration::from_millis(100)).await;
        assert_eq!(container.status().await, Status::Running);
        
        // クリーンアップを実行
        container.cleanup().await?;
        assert_eq!(container.status().await, Status::Stopped);
        
        // 実行完了を待つ
        handle.abort();
        
        Ok(())
    }

    #[tokio::test]
    async fn test_container_cancel() -> Result<()> {
        let container = setup_test_container().await?;
        
        // コンテナの実行
        let handle = tokio::spawn({
            let container = container.clone();
            async move {
                container.run().await
            }
        });

        // 少し待ってからキャンセル
        sleep(Duration::from_millis(100)).await;
        assert_eq!(container.status().await, Status::Running);
        
        // キャンセルの実行
        handle.abort();
        sleep(Duration::from_millis(100)).await;
        
        Ok(())
    }

    #[tokio::test]
    async fn test_python_execution() -> Result<()> {
        let container = setup_language_container(
            "python",
            "test.py",
            vec!["python".to_string(), "test.py".to_string()]
        ).await?;
        
        assert_eq!(container.status().await, Status::Created);
        
        let handle = tokio::spawn({
            let container = container.clone();
            async move {
                container.run().await
            }
        });

        sleep(Duration::from_millis(100)).await;
        assert_eq!(container.status().await, Status::Running);
        
        container.cleanup().await?;
        assert_eq!(container.status().await, Status::Stopped);
        
        handle.abort();
        Ok(())
    }

    #[tokio::test]
    async fn test_rust_execution() -> Result<()> {
        let container = setup_language_container(
            "rust",
            "main.rs",
            vec!["cargo".to_string(), "run".to_string()]
        ).await?;
        
        assert_eq!(container.status().await, Status::Created);
        
        let handle = tokio::spawn({
            let container = container.clone();
            async move {
                container.run().await
            }
        });

        sleep(Duration::from_millis(100)).await;
        assert_eq!(container.status().await, Status::Running);
        
        container.cleanup().await?;
        assert_eq!(container.status().await, Status::Stopped);
        
        handle.abort();
        Ok(())
    }

    #[tokio::test]
    async fn test_compilation_error() -> Result<()> {
        let container = setup_language_container(
            "rust",
            "invalid.rs",
            vec!["rustc".to_string(), "invalid.rs".to_string()]
        ).await?;
        
        let handle = tokio::spawn({
            let container = container.clone();
            async move {
                let result = container.run().await;
                assert!(result.is_err()); // コンパイルエラーを期待
                result
            }
        });

        sleep(Duration::from_millis(100)).await;
        
        // エラー状態の確認
        match container.status().await {
            Status::Failed(_) => (),
            _ => panic!("コンパイルエラーが検出されませんでした"),
        }
        
        handle.abort();
        Ok(())
    }

    #[tokio::test]
    async fn test_runtime_error() -> Result<()> {
        let container = setup_language_container(
            "python",
            "error.py",
            vec!["python".to_string(), "-c".to_string(), "raise Exception('Runtime Error')".to_string()]
        ).await?;
        
        let handle = tokio::spawn({
            let container = container.clone();
            async move {
                let result = container.run().await;
                assert!(result.is_err()); // 実行時エラーを期待
                result
            }
        });

        sleep(Duration::from_millis(100)).await;
        
        // エラー状態の確認
        match container.status().await {
            Status::Failed(_) => (),
            _ => panic!("実行時エラーが検出されませんでした"),
        }
        
        handle.abort();
        Ok(())
    }

    #[tokio::test]
    async fn test_timeout_handling() -> Result<()> {
        let container = setup_language_container(
            "python",
            "infinite.py",
            vec!["python".to_string(), "-c".to_string(), "while True: pass".to_string()]
        ).await?;
        
        let handle = tokio::spawn({
            let container = container.clone();
            async move {
                container.run().await
            }
        });

        // タイムアウト時間待機
        sleep(Duration::from_secs(2)).await;
        
        // 強制終了
        container.cancel().await;
        
        // 状態確認
        assert_eq!(container.status().await, Status::Stopped);
        
        handle.abort();
        Ok(())
    }

    #[tokio::test]
    async fn test_python_with_source_file() -> Result<()> {
        let source_file = "test/solution.py";
        let container = setup_language_container(
            "python",
            source_file,
            vec!["python".to_string(), source_file.to_string()]
        ).await?;
        
        assert_eq!(container.status().await, Status::Created);
        assert_eq!(
            container.working_dir(),
            PathBuf::from("/workspace/test")
        );
        
        let handle = tokio::spawn({
            let container = container.clone();
            async move {
                container.run().await
            }
        });

        sleep(Duration::from_millis(100)).await;
        assert_eq!(container.status().await, Status::Running);
        
        container.cleanup().await?;
        assert_eq!(container.status().await, Status::Stopped);
        
        handle.abort();
        Ok(())
    }

    #[tokio::test]
    async fn test_rust_with_source_file() -> Result<()> {
        let source_file = "src/main.rs";
        let container = setup_language_container(
            "rust",
            source_file,
            vec!["cargo".to_string(), "run".to_string(), "--manifest-path".to_string(), "Cargo.toml".to_string()]
        ).await?;
        
        assert_eq!(container.status().await, Status::Created);
        assert_eq!(
            container.working_dir(),
            PathBuf::from("/workspace/src")
        );
        
        let handle = tokio::spawn({
            let container = container.clone();
            async move {
                container.run().await
            }
        });

        sleep(Duration::from_millis(100)).await;
        assert_eq!(container.status().await, Status::Running);
        
        container.cleanup().await?;
        assert_eq!(container.status().await, Status::Stopped);
        
        handle.abort();
        Ok(())
    }
} 