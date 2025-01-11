use std::collections::{HashMap, HashSet, VecDeque};
use std::sync::Arc;
use tokio::sync::Mutex;
use tokio::task::JoinHandle;
use crate::container::{Container, ContainerBuilder, Network, Buffer, ContainerState};
use crate::container::communication::message::Message;
use anyhow::Result;

/// コンテナの実行を調整・制御するオーケストレーター
pub struct ContainerOrchestrator {
    /// 管理下のコンテナ
    containers: Arc<Mutex<HashMap<String, Container>>>,
    /// コンテナ間の通信リンク
    links: Arc<Mutex<HashMap<String, HashSet<String>>>>,
    /// 共有ネットワーク
    network: Arc<Network>,
    /// 実行中のタスクハンドル
    running_tasks: Arc<Mutex<HashMap<String, JoinHandle<Result<()>>>>>,
    /// メッセージ履歴
    message_history: Arc<Mutex<VecDeque<Message>>>,
    /// 履歴の最大保持数
    max_history_size: usize,
}

impl ContainerOrchestrator {
    /// 新しいオーケストレーターを作成
    pub fn new() -> Self {
        Self::with_history_size(1000) // デフォルトで1000件保持
    }

    /// 履歴サイズを指定してオーケストレーターを作成
    pub fn with_history_size(max_history_size: usize) -> Self {
        Self {
            containers: Arc::new(Mutex::new(HashMap::new())),
            links: Arc::new(Mutex::new(HashMap::new())),
            network: Arc::new(Network::new()),
            running_tasks: Arc::new(Mutex::new(HashMap::new())),
            message_history: Arc::new(Mutex::new(VecDeque::with_capacity(max_history_size))),
            max_history_size,
        }
    }

    /// コンテナを追加
    pub async fn add_container(
        &self,
        language: &str,
        source_file: &str,
        args: Vec<&str>,
    ) -> Result<Container> {
        let container = ContainerBuilder::new()
            .with_network(self.network.clone())
            .with_buffer(Arc::new(Buffer::new()))
            .build_for_language(language, source_file, args)
            .await?;

        let mut containers = self.containers.lock().await;
        containers.insert(container.id().to_string(), container.clone());
        
        Ok(container)
    }

    /// コンテナ間の通信リンクを設定
    pub async fn link(&self, from: &str, to: &str) -> &Self {
        let mut links = self.links.lock().await;
        links.entry(from.to_string())
            .or_insert_with(HashSet::new)
            .insert(to.to_string());
        self
    }

    /// メッセージを送信し、履歴に保存
    pub async fn send_message(&self, message: &Message) -> Result<()> {
        if let Some(to) = &message.to {
            self.network.send(&message.from, to, &message.content).await?;
            self.add_to_history(message.clone()).await;
        }
        Ok(())
    }

    /// メッセージをブロードキャストし、履歴に保存
    pub async fn broadcast(&self, message: &Message) -> Result<()> {
        self.network.broadcast(&message.from, &message.content).await?;
        self.add_to_history(message.clone()).await;
        Ok(())
    }

    /// メッセージを履歴に追加
    async fn add_to_history(&self, message: Message) {
        let mut history = self.message_history.lock().await;
        if history.len() >= self.max_history_size {
            history.pop_front(); // 最も古いメッセージを削除
        }
        history.push_back(message);
    }

    /// 全メッセージ履歴を取得
    pub async fn get_message_history(&self) -> Vec<Message> {
        let history = self.message_history.lock().await;
        history.iter().cloned().collect()
    }

    /// 特定のコンテナに関連するメッセージ履歴を取得
    pub async fn get_container_messages(&self, container_id: &str) -> Vec<Message> {
        let history = self.message_history.lock().await;
        history
            .iter()
            .filter(|msg| {
                msg.from == container_id || 
                msg.to.as_ref().map_or(false, |to| to == container_id)
            })
            .cloned()
            .collect()
    }

    /// 特定の種類のメッセージ履歴を取得
    pub async fn get_messages_by_kind(&self, kind: MessageKind) -> Vec<Message> {
        let history = self.message_history.lock().await;
        history
            .iter()
            .filter(|msg| msg.kind == kind)
            .cloned()
            .collect()
    }

    /// 履歴をクリア
    pub async fn clear_history(&self) {
        let mut history = self.message_history.lock().await;
        history.clear();
    }

    /// 全コンテナを実行
    pub async fn run_all(&self) -> Result<()> {
        let containers = self.containers.lock().await;
        let mut tasks = self.running_tasks.lock().await;

        for container in containers.values() {
            let container = container.clone();
            let handle = tokio::spawn(async move {
                container.run().await
            });
            tasks.insert(container.id().to_string(), handle);
        }
        Ok(())
    }

    /// 全コンテナの終了を待機
    /// 
    /// # 動作
    /// - 全てのコンテナが終了するまで待機
    /// - 待機中もメッセージの送受信は可能
    /// - 終了したコンテナは自動的にクリーンアップ
    pub async fn wait_all(&self) -> Result<()> {
        let mut tasks = self.running_tasks.lock().await;
        let mut completed = HashSet::new();

        // 全てのタスクが完了するまで待機
        while !tasks.is_empty() {
            let mut to_remove = Vec::new();

            for (id, handle) in tasks.iter() {
                if handle.is_finished() {
                    // タスクが完了したらクリーンアップ
                    if let Some(container) = self.get_container(id).await {
                        container.cleanup().await?;
                    }
                    to_remove.push(id.clone());
                    completed.insert(id.clone());
                }
            }

            // 完了したタスクを削除
            for id in to_remove {
                tasks.remove(&id);
            }

            // 少し待機して再チェック
            tokio::time::sleep(tokio::time::Duration::from_millis(100)).await;
        }

        // コンテナの状態を更新
        let mut containers = self.containers.lock().await;
        for id in completed {
            if let Some(container) = containers.get(&id) {
                if container.state().await == ContainerState::Running {
                    // 状態を完了に更新
                    container.set_state(ContainerState::Completed).await?;
                }
            }
        }

        Ok(())
    }

    /// コンテナの状態を確認
    pub async fn is_running(&self, id: &str) -> bool {
        if let Some(container) = self.get_container(id).await {
            return container.state().await == ContainerState::Running;
        }
        false
    }

    /// コンテナを取得
    pub async fn get_container(&self, id: &str) -> Option<Container> {
        let containers = self.containers.lock().await;
        containers.get(id).cloned()
    }

    /// 全コンテナをクリーンアップ
    pub async fn cleanup(&self) -> Result<()> {
        let mut containers = self.containers.lock().await;
        for container in containers.values() {
            container.cleanup().await?;
        }
        containers.clear();
        Ok(())
    }

    /// 孤立したコンテナ（リンクのない）を取得
    pub async fn get_isolated_containers(&self) -> Vec<Container> {
        let containers = self.containers.lock().await;
        let links = self.links.lock().await;
        
        containers
            .values()
            .filter(|container| {
                let id = container.id();
                !links.contains_key(id) && 
                !links.values().any(|targets| targets.contains(id))
            })
            .cloned()
            .collect()
    }

    /// オーケストレーターの状態サマリーを取得
    pub async fn get_status_summary(&self) -> OrchestratorStatus {
        let containers = self.containers.lock().await;
        let links = self.links.lock().await;
        let history = self.message_history.lock().await;

        OrchestratorStatus {
            total_containers: containers.len(),
            running_containers: containers
                .values()
                .filter(|c| futures::executor::block_on(c.state()) == ContainerState::Running)
                .count(),
            isolated_containers: self.get_isolated_containers().await.len(),
            total_links: links.values().map(|targets| targets.len()).sum(),
            total_messages: history.len(),
            message_types: self.count_message_types().await,
        }
    }

    /// メッセージ種類ごとの数を集計
    async fn count_message_types(&self) -> HashMap<MessageKind, usize> {
        let history = self.message_history.lock().await;
        let mut counts = HashMap::new();
        
        for message in history.iter() {
            *counts.entry(message.kind.clone()).or_insert(0) += 1;
        }
        
        counts
    }

    /// コンテナ間のリンク関係を取得
    pub async fn get_network_topology(&self) -> NetworkTopology {
        let containers = self.containers.lock().await;
        let links = self.links.lock().await;
        
        NetworkTopology {
            nodes: containers.values().map(|c| c.id().to_string()).collect(),
            edges: links
                .iter()
                .flat_map(|(from, targets)| {
                    targets.iter().map(move |to| (from.clone(), to.clone()))
                })
                .collect(),
        }
    }
}

/// オーケストレーターの状態サマリー
#[derive(Debug, Clone)]
pub struct OrchestratorStatus {
    /// 全コンテナ数
    pub total_containers: usize,
    /// 実行中のコンテナ数
    pub running_containers: usize,
    /// 孤立したコンテナ数
    pub isolated_containers: usize,
    /// 総リンク数
    pub total_links: usize,
    /// 総メッセージ数
    pub total_messages: usize,
    /// メッセージ種類ごとの数
    pub message_types: HashMap<MessageKind, usize>,
}

/// ネットワークトポロジー
#[derive(Debug, Clone)]
pub struct NetworkTopology {
    /// ノード（コンテナID）
    pub nodes: Vec<String>,
    /// エッジ（リンク）
    pub edges: Vec<(String, String)>,
}

#[cfg(test)]
mod tests {
    use super::*;
    use tokio::time::Duration;

    #[tokio::test]
    async fn test_container_orchestrator() -> Result<()> {
        let orchestrator = ContainerOrchestrator::new();

        // コンテナを追加
        let container1 = orchestrator
            .add_container("python", "test1.py", vec!["python", "test1.py"])
            .await?;
        let container2 = orchestrator
            .add_container("python", "test2.py", vec!["python", "test2.py"])
            .await?;

        // リンクを設定
        orchestrator
            .link(container1.id(), container2.id())
            .link(container2.id(), container1.id());

        // メッセージを送信
        orchestrator.send_message(container1.id(), container2.id(), "Test message").await?;

        // クリーンアップ
        orchestrator.cleanup().await?;

        Ok(())
    }

    #[tokio::test]
    async fn test_wait_all_with_messaging() -> Result<()> {
        let orchestrator = ContainerOrchestrator::new();

        // コンテナを追加
        let container1 = orchestrator
            .add_container("python", "test1.py", vec!["python", "test1.py"])
            .await?;
        let container2 = orchestrator
            .add_container("python", "test2.py", vec!["python", "test2.py"])
            .await?;

        // リンクを設定
        orchestrator
            .link(container1.id(), container2.id())
            .link(container2.id(), container1.id());

        // コンテナを実行
        orchestrator.run_all().await?;

        // 別タスクでメッセージ送信をテスト
        let orchestrator_clone = orchestrator.clone();
        let message_task = tokio::spawn(async move {
            // コンテナが実行中の間メッセージを送信
            while orchestrator_clone.is_running(container1.id()).await {
                orchestrator_clone
                    .send_message(container1.id(), container2.id(), "Test message")
                    .await?;
                tokio::time::sleep(Duration::from_millis(100)).await;
            }
            Ok::<(), anyhow::Error>(())
        });

        // 終了を待機
        orchestrator.wait_all().await?;
        message_task.await??;

        Ok(())
    }

    #[tokio::test]
    async fn test_status_summary() -> Result<()> {
        let orchestrator = ContainerOrchestrator::new();

        // コンテナを追加
        let container1 = orchestrator
            .add_container("python", "test1.py", vec!["python", "test1.py"])
            .await?;
        let container2 = orchestrator
            .add_container("python", "test2.py", vec!["python", "test2.py"])
            .await?;
        let container3 = orchestrator
            .add_container("python", "test3.py", vec!["python", "test3.py"])
            .await?;

        // リンクを設定（container3は孤立）
        orchestrator
            .link(container1.id(), container2.id())
            .link(container2.id(), container1.id());

        // 状態を確認
        let status = orchestrator.get_status_summary().await;
        assert_eq!(status.total_containers, 3);
        assert_eq!(status.isolated_containers, 1);
        assert_eq!(status.total_links, 2);

        // トポロジーを確認
        let topology = orchestrator.get_network_topology().await;
        assert_eq!(topology.nodes.len(), 3);
        assert_eq!(topology.edges.len(), 2);

        Ok(())
    }
} 