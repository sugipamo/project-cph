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
    use bytes::Bytes;

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

    #[tokio::test]
    async fn test_container_with_env_vars() -> Result<()> {
        let container = setup_language_container(
            "python",
            "env_test.py",
            vec!["python".to_string(), "-c".to_string(), "import os; print(os.environ['TEST_VAR'])".to_string()]
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
    async fn test_parallel_container_execution() -> Result<()> {
        let mut handles = vec![];
        let mut containers = vec![];

        // 複数のコンテナを作成
        for i in 0..3 {
            let container = setup_language_container(
                "python",
                &format!("test{}.py", i),
                vec!["python".to_string(), "-c".to_string(), "print('test')".to_string()]
            ).await?;
            containers.push(container);
        }

        // 並列実行
        for container in containers {
            let handle = tokio::spawn({
                let container = container.clone();
                async move {
                    container.run().await
                }
            });
            handles.push(handle);
        }

        // すべての実行完了を待つ
        for handle in handles {
            handle.abort();
        }

        Ok(())
    }

    #[tokio::test]
    async fn test_container_output_buffering() -> Result<()> {
        use std::path::PathBuf;
        use cph::container::communication::Network;
        
        let container_id = "test-container".to_string();
        let runtime = MockRuntime::new(container_id.clone());
        let network = Arc::new(Network::new());
        let buffer = Arc::new(Buffer::with_max_size(1024));
        
        let config = Config::new(
            container_id.clone(),
            "python".to_string(),
            PathBuf::from("/workspace"),
            vec!["python".to_string(), "-c".to_string(), "print('test')".to_string()]
        );

        let container = Container::with_runtime(
            config,
            network,
            buffer.clone(),
            runtime
        ).await?;

        // 出力のシミュレーション
        buffer.append(&container.id(), Bytes::from("Line 1\n")).await?;
        buffer.append(&container.id(), Bytes::from("Line 2\n")).await?;
        buffer.append(&container.id(), Bytes::from("Line 3\n")).await?;

        // バッファの内容を確認
        let output = buffer.get_output(&container.id()).await.unwrap();
        let output_str: String = output.iter()
            .map(|bytes| String::from_utf8_lossy(bytes).to_string())
            .collect();

        let expected_output = "Line 1\nLine 2\nLine 3\n";
        assert_eq!(output_str, expected_output, "バッファの出力が期待値と一致しません");

        Ok(())
    }

    #[tokio::test]
    async fn test_container_resource_cleanup() -> Result<()> {
        let container = setup_language_container(
            "python",
            "cleanup_test.py",
            vec!["python".to_string(), "-c".to_string(), "print('test')".to_string()]
        ).await?;

        // コンテナを実行
        let handle = tokio::spawn({
            let container = container.clone();
            async move {
                container.run().await
            }
        });

        sleep(Duration::from_millis(100)).await;
        
        // 強制終了してクリーンアップ
        container.cancel().await;
        container.cleanup().await?;

        // リソースが解放されていることを確認
        assert_eq!(container.status().await, Status::Stopped);
        
        // バッファがクリアされていることを確認
        let buffer = container.buffer();
        assert_eq!(buffer.get_size(&container.id()).await, 0);

        handle.abort();
        Ok(())
    }
} 