use std::collections::{HashMap, HashSet, VecDeque};
use std::sync::Arc;
use tokio::sync::Mutex;
use tokio::time::Duration;
use crate::container::runtime::Container;
use crate::container::runtime::builder::ContainerBuilder;
use crate::container::runtime::container::ContainerState;
use crate::container::communication::transport::Network;
use crate::container::communication::protocol::{Message, MessageKind};
use anyhow::Result;

#[derive(Clone)]
pub struct ContainerOrchestrator {
    containers: Arc<Mutex<HashMap<String, Container>>>,
    links: Arc<Mutex<HashMap<String, HashSet<String>>>>,
    network: Arc<Network>,
    message_history: Arc<Mutex<VecDeque<Message>>>,
    max_history_size: usize,
}

impl ContainerOrchestrator {
    pub fn new() -> Self {
        Self {
            containers: Arc::new(Mutex::new(HashMap::new())),
            links: Arc::new(Mutex::new(HashMap::new())),
            network: Arc::new(Network::new()),
            message_history: Arc::new(Mutex::new(VecDeque::new())),
            max_history_size: 1000,
        }
    }

    pub async fn add_container(&self, language: &str, source_file: &str, args: Vec<String>) -> Result<Container> {
        let container = ContainerBuilder::new()
            .build_for_language(language, source_file, args)
            .await?;
        let mut containers = self.containers.lock().await;
        containers.insert(container.id().to_string(), container.clone());
        Ok(container)
    }

    pub async fn link(&self, from: &str, to: &str) -> Result<&Self> {
        let mut links = self.links.lock().await;
        links.entry(from.to_string())
            .or_insert_with(HashSet::new)
            .insert(to.to_string());
        Ok(self)
    }

    pub async fn send_message(&self, message: Message) -> Result<()> {
        let containers = self.containers.lock().await;
        if let Some(_) = containers.get(&message.to) {
            self.network.send(&message.from, &message.to, message.clone()).await?;
            
            let mut history = self.message_history.lock().await;
            if history.len() >= self.max_history_size {
                history.pop_front();
            }
            history.push_back(message);
        }
        Ok(())
    }

    pub async fn broadcast(&self, message: Message) -> Result<()> {
        self.network.broadcast(&message.from, message.clone()).await?;
        
        let mut history = self.message_history.lock().await;
        if history.len() >= self.max_history_size {
            history.pop_front();
        }
        history.push_back(message);
        Ok(())
    }

    pub async fn run_all(&self) -> Result<()> {
        let container_ids: Vec<String> = {
            let containers = self.containers.lock().await;
            containers.keys().cloned().collect()
        };

        let mut handles = Vec::new();
        
        // 各コンテナを個別に取得して実行
        for id in container_ids {
            if let Some(container) = self.get_container(&id).await {
                let handle = tokio::spawn(async move {
                    container.run().await
                });
                handles.push((id, handle));
            }
        }
        
        // タイムアウト付きで実行結果を待機（5秒）
        let timeout = Duration::from_secs(5);
        let mut errors = Vec::new();
        
        for (id, handle) in handles {
            match tokio::time::timeout(timeout, handle).await {
                Ok(result) => {
                    if let Err(e) = result? {
                        errors.push(format!("コンテナ {} の実行に失敗: {}", id, e));
                    }
                }
                Err(_) => {
                    errors.push(format!("コンテナ {} の実行がタイムアウトしました", id));
                }
            }
        }
        
        if !errors.is_empty() {
            return Err(anyhow::anyhow!("コンテナの実行に失敗:\n{}", errors.join("\n")));
        }
        
        Ok(())
    }

    pub async fn wait_all(&self) -> Result<()> {
        let container_ids: Vec<String> = {
            let containers = self.containers.lock().await;
            containers.keys().cloned().collect()
        };

        let timeout = Duration::from_secs(5); // 5秒のタイムアウト
        let start_time = std::time::Instant::now();

        for id in container_ids {
            loop {
                if let Some(container) = self.get_container(&id).await {
                    if container.status().await == ContainerState::Completed {
                        break;
                    }
                }

                if start_time.elapsed() > timeout {
                    return Err(anyhow::anyhow!("コンテナの待機がタイムアウトしました: {}", id));
                }

                tokio::time::sleep(Duration::from_millis(100)).await;
            }
        }
        Ok(())
    }

    pub async fn get_container(&self, id: &str) -> Option<Container> {
        let containers = self.containers.lock().await;
        containers.get(id).cloned()
    }

    pub async fn get_isolated_containers(&self) -> Vec<String> {
        let containers = self.containers.lock().await;
        let links = self.links.lock().await;
        
        containers
            .keys()
            .filter(|id| {
                !links.contains_key(*id) && 
                !links.values().any(|targets| targets.contains(*id))
            })
            .cloned()
            .collect()
    }

    pub async fn get_status_summary(&self) -> OrchestratorStatus {
        let containers = self.containers.lock().await;
        let links = self.links.lock().await;
        let history = self.message_history.lock().await;
        
        let mut message_counts = HashMap::new();
        for message in history.iter() {
            *message_counts.entry(message.kind.clone()).or_insert(0) += 1;
        }
        
        OrchestratorStatus {
            total_containers: containers.len(),
            running_containers: containers.len(),
            isolated_containers: self.get_isolated_containers().await.len(),
            total_links: links.values().map(|targets| targets.len()).sum(),
            total_messages: history.len(),
            message_counts,
        }
    }

    pub async fn add_container_with_builder(
        &self,
        builder: ContainerBuilder,
        language: &str,
        source_file: &str,
        args: Vec<String>
    ) -> Result<Container> {
        let container = builder
            .build_for_language(language, source_file, args)
            .await?;
        let mut containers = self.containers.lock().await;
        containers.insert(container.id().to_string(), container.clone());
        Ok(container)
    }
}

#[derive(Debug, Clone)]
pub struct OrchestratorStatus {
    pub total_containers: usize,
    pub running_containers: usize,
    pub isolated_containers: usize,
    pub total_links: usize,
    pub total_messages: usize,
    pub message_counts: HashMap<MessageKind, usize>,
} 