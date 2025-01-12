use std::sync::Arc;
use anyhow::{Result, anyhow};
use tokio::sync::Mutex;
use crate::container::{
    communication::transport::Network,
    io::buffer::Buffer,
};
use super::{container::Container, config::Config, containerd::ContainerdRuntime, Runtime};

pub struct ParallelExecutor {
    runtime: Arc<dyn Runtime>,
    #[allow(dead_code)]
    network: Arc<Network>,
    #[allow(dead_code)]
    buffer: Arc<Buffer>,
    containers: Arc<Mutex<Vec<Container>>>,
}

impl ParallelExecutor {
    /// 新しいオーケストレーターを作成します。
    ///
    /// # Returns
    /// * `Ok(Self)` - オーケストレーターの作成に成功
    /// * `Err(_)` - オーケストレーターの作成に失敗
    ///
    /// # Errors
    /// * ランタイムの初期化に失敗した場合
    pub async fn new() -> Result<Self> {
        let runtime = Arc::new(ContainerdRuntime::new().await?);
        Self::with_runtime(runtime)
    }

    /// 指定されたランタイムでオーケストレーターを作成します。
    ///
    /// # Arguments
    /// * `runtime` - コンテナランタイム
    ///
    /// # Returns
    /// * `Ok(Self)` - オーケストレーターの作成に成功
    /// * `Err(_)` - オーケストレーターの作成に失敗
    ///
    /// # Errors
    /// * ネットワークの初期化に失敗した場合
    pub fn with_runtime(runtime: Arc<dyn Runtime>) -> Result<Self> {
        Ok(Self {
            runtime,
            network: Arc::new(Network::new()),
            buffer: Arc::new(Buffer::new()),
            containers: Arc::new(Mutex::new(Vec::new())),
        })
    }

    /// コンテナを実行します。
    ///
    /// # Arguments
    /// * `configs` - コンテナの設定のリスト
    ///
    /// # Returns
    /// * `Ok(())` - すべてのコンテナの実行に成功
    /// * `Err(_)` - いずれかのコンテナの実行に失敗
    ///
    /// # Errors
    /// * コンテナの作成に失敗した場合
    /// * コンテナの起動に失敗した場合
    /// * コンテナの実行中にエラーが発生した場合
    pub async fn execute(&self, configs: Vec<Config>) -> Result<()> {
        let mut handles = vec![];
        
        for config in configs {
            let runtime = Arc::clone(&self.runtime);
            let containers_ref = Arc::clone(&self.containers);
            
            let handle = tokio::spawn(async move {
                let container = Container::new(runtime, config);
                
                // コンテナの追加は最小限のロック時間で行う
                {
                    let mut containers = containers_ref.lock().await;
                    containers.push(container.clone());
                }
                
                // コンテナの実行中にエラーが発生した場合、適切なエラーメッセージを返す
                container.run().await.map_err(|e| {
                    anyhow!("コンテナの実行中にエラーが発生しました: {}", e)
                })?;

                Ok::<_, anyhow::Error>(())
            });
            
            handles.push(handle);
        }

        // 全てのタスクの完了を待ち、エラーがあれば適切に処理する
        for handle in handles {
            match handle.await {
                Ok(result) => {
                    result.map_err(|e| anyhow!("コンテナの実行に失敗しました: {}", e))?;
                }
                Err(e) => {
                    return Err(anyhow!("タスクの実行に失敗しました: {}", e));
                }
            }
        }

        Ok(())
    }

    /// コンテナをクリーンアップします。
    ///
    /// # Returns
    /// * `Ok(())` - すべてのコンテナのクリーンアップに成功
    /// * `Err(_)` - いずれかのコンテナのクリーンアップに失敗
    ///
    /// # Errors
    /// * コンテナの停止に失敗した場合
    /// * コンテナの削除に失敗した場合
    pub async fn cleanup(&self) -> Result<()> {
        let containers = {
            let mut containers = self.containers.lock().await;
            std::mem::take(&mut *containers)
        };

        let mut cleanup_errors = Vec::new();
        for container in containers {
            if let Err(e) = container.cancel().await {
                cleanup_errors.push(format!("コンテナのクリーンアップに失敗: {e}"));
            }
        }

        if cleanup_errors.is_empty() {
            Ok(())
        } else {
            Err(anyhow!("クリーンアップエラー: {}", cleanup_errors.join(", ")))
        }
    }
} 