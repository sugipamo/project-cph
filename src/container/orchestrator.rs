use std::collections::{HashMap, HashSet, VecDeque};
use std::sync::Arc;
use tokio::sync::Mutex;
use tokio::time::Duration;
use crate::container::runtime::Container;
use crate::container::runtime::Builder;
use crate::container::runtime::State;
use crate::container::communication::transport::Network;
use crate::container::communication::protocol::{Message, MessageKind};
use anyhow::Result;

#[derive(Clone)]
pub struct Orchestrator {
    containers: Arc<Mutex<HashMap<String, Container>>>,
    links: Arc<Mutex<HashMap<String, HashSet<String>>>>,
    network: Arc<Network>,
    message_history: Arc<Mutex<VecDeque<Message>>>,
    max_history_size: usize,
    message_counts: Arc<Mutex<HashMap<MessageKind, usize>>>,
}

impl Orchestrator {
    #[must_use]
    pub fn new() -> Self {
        Self {
            containers: Arc::new(Mutex::new(HashMap::new())),
            links: Arc::new(Mutex::new(HashMap::new())),
            network: Arc::new(Network::new()),
            message_history: Arc::new(Mutex::new(VecDeque::new())),
            max_history_size: 1000,
            message_counts: Arc::new(Mutex::new(HashMap::new())),
        }
    }

    /// コンテナを追加します
    /// 
    /// # Errors
    /// - コンテナの作成に失敗した場合
    /// - コンテナの登録に失敗した場合
    pub async fn add_container(&self, language: &str, source_file: &str, args: Vec<String>) -> Result<Container> {
        let container = Builder::new()
            .build_for_language(language, source_file, args)?;
        let mut containers = self.containers.lock().await;
        containers.insert(container.id().to_string(), container.clone());
        Ok(container)
    }

    /// コンテナ間のリンクを作成します
    /// 
    /// # Errors
    /// - リンクの作成に失敗した場合
    pub async fn link(&self, from: &str, to: &str) -> Result<&Self> {
        println!("Orchestrator: リンク作成 {from} -> {to}");
        self.links.lock().await
            .entry(from.to_string())
            .or_insert_with(HashSet::new)
            .insert(to.to_string());
        Ok(self)
    }

    /// メッセージを送信します
    /// 
    /// # Errors
    /// - メッセージの送信に失敗した場合
    /// - 履歴の更新に失敗した場合
    pub async fn send_message(&self, message: Message) -> Result<()> {
        println!("Orchestrator: メッセージ送信 ({message:?})");
        
        let container_exists = self.containers.lock().await.get(&message.to).is_some();
        if container_exists {
            self.network.send(&message.from, &message.to, message.clone()).await?;
            
            {
                let mut history = self.message_history.lock().await;
                if history.len() >= self.max_history_size {
                    history.pop_front();
                }
                history.push_back(message.clone());
            }
            println!("Orchestrator: メッセージ履歴に追加");

            // メッセージカウントを更新
            {
                *self.message_counts.lock().await
                    .entry(message.kind)
                    .or_insert(0) += 1;
                println!("Orchestrator: メッセージカウント更新");
            }
        } else {
            println!("Orchestrator: 宛先コンテナが見つかりません: {}", message.to);
        }
        Ok(())
    }

    /// メッセージをブロードキャストします
    /// 
    /// # Errors
    /// - メッセージの送信に失敗した場合
    /// - 履歴の更新に失敗した場合
    pub async fn broadcast(&self, message: Message) -> Result<()> {
        self.network.broadcast(&message.from, message.clone()).await?;
        
        {
            let mut history = self.message_history.lock().await;
            if history.len() >= self.max_history_size {
                history.pop_front();
            }
            history.push_back(message);
        }
        Ok(())
    }

    /// すべてのコンテナを実行します
    /// 
    /// # Errors
    /// - コンテナの実行に失敗した場合
    /// - タイムアウトが発生した場合
    pub async fn run_all(&self) -> Result<()> {
        println!("run_all: 開始");
        let container_ids: Vec<String> = {
            let ids = self.containers.lock().await
                .keys()
                .cloned()
                .collect();
            println!("run_all: コンテナID一覧: {ids:?}");
            ids
        };

        let mut handles = Vec::new();
        
        for id in &container_ids {
            println!("run_all: コンテナ {id} の実行準備");
            if let Some(container) = self.get_container(id).await {
                let handle = tokio::spawn(async move {
                    println!("run_all: コンテナ {} の実行開始", container.id());
                    let result = container.run().await;
                    println!("run_all: コンテナ {} の実行完了: {:?}", container.id(), result.is_ok());
                    result
                });
                handles.push((id.clone(), handle));
            }
        }
        
        println!("run_all: 全コンテナの実行待機開始");
        let timeout = Duration::from_secs(5);
        let results = tokio::time::timeout(
            timeout,
            futures::future::join_all(handles.into_iter().map(|(id, handle)| async move {
                match handle.await {
                    Ok(result) => (id, result),
                    Err(e) => {
                        println!("run_all: コンテナ {id} でパニック発生: {e}");
                        (id, Err(anyhow::anyhow!("タスクのパニック: {}", e)))
                    }
                }
            }))
        ).await.map_err(|_| {
            println!("run_all: タイムアウト発生");
            anyhow::anyhow!("コンテナの実行がタイムアウトしました")
        })?;

        let errors: Vec<_> = results
            .into_iter()
            .filter_map(|(id, result)| {
                result.err().map(|e| {
                    let msg = format!("コンテナ {id} の実行に失敗: {e}");
                    println!("run_all: {msg}");
                    msg
                })
            })
            .collect();

        if !errors.is_empty() {
            println!("run_all: エラーあり");
            return Err(anyhow::anyhow!("コンテナの実行に失敗:\n{}", errors.join("\n")));
        }

        println!("run_all: 正常終了");
        Ok(())
    }

    /// すべてのコンテナの完了を待機します
    /// 
    /// # Errors
    /// - コンテナの待機に失敗した場合
    /// - タイムアウトが発生した場合
    pub async fn wait_all(&self) -> Result<()> {
        println!("wait_all: 開始");
        let container_ids: Vec<String> = {
            let containers = self.containers.lock().await;
            let ids = containers.keys().cloned().collect();
            println!("wait_all: コンテナID一覧: {ids:?}");
            ids
        };

        let timeout = Duration::from_secs(5);
        let start_time = std::time::Instant::now();

        let wait_futures = container_ids.iter().map(|id| {
            let id = id.clone();
            async move {
                println!("wait_all: コンテナ {id} の待機開始");
                loop {
                    if let Some(container) = self.get_container(&id).await {
                        let status = container.status().await;
                        println!("wait_all: コンテナ {id} の状態: {status:?}");
                        if status == State::Completed {
                            println!("wait_all: コンテナ {id} が完了");
                            return Ok(());
                        }
                    }

                    if start_time.elapsed() > timeout {
                        println!("wait_all: コンテナ {id} がタイムアウト");
                        return Err(anyhow::anyhow!("コンテナの待機がタイムアウトしました: {}", id));
                    }

                    tokio::time::sleep(Duration::from_millis(100)).await;
                }
            }
        });

        println!("wait_all: 全コンテナの完了待機開始");
        let results = futures::future::join_all(wait_futures).await;
        
        let error_messages: Vec<_> = results
            .into_iter()
            .filter_map(|r| r.err().map(|e| {
                let msg = e.to_string();
                println!("wait_all: エラー: {msg}");
                msg
            }))
            .collect();

        if !error_messages.is_empty() {
            println!("wait_all: エラーあり");
            return Err(anyhow::anyhow!("コンテナの待機に失敗:\n{}", error_messages.join("\n")));
        }

        println!("wait_all: 正常終了");
        Ok(())
    }

    pub async fn get_container(&self, id: &str) -> Option<Container> {
        let containers = self.containers.lock().await;
        containers.get(id).cloned()
    }

    pub async fn get_isolated_containers(&self) -> Vec<String> {
        println!("Orchestrator: 孤立コンテナの検索開始");
        let containers = self.containers.lock().await;
        let links = self.links.lock().await;
        
        let isolated = containers
            .keys()
            .filter(|id| {
                let is_isolated = !links.contains_key(*id) && 
                    !links.values().any(|targets| targets.contains(*id));
                println!("Orchestrator: コンテナ {} は孤立{}", id, if is_isolated { "しています" } else { "していません" });
                is_isolated
            })
            .cloned()
            .collect();
        
        println!("Orchestrator: 孤立コンテナの検索完了");
        isolated
    }

    pub async fn get_status_summary(&self) -> OrchestratorStatus {
        println!("Orchestrator: ステータスサマリー取得開始");
        
        // 孤立コンテナの数を先に取得
        let isolated_count = self.get_isolated_containers().await.len();
        println!("Orchestrator: 孤立コンテナ数 = {isolated_count}");

        // 他の情報を取得
        let containers = self.containers.lock().await;
        let links = self.links.lock().await;
        let history = self.message_history.lock().await;
        let counts = self.message_counts.lock().await;
        
        let status = OrchestratorStatus {
            total_containers: containers.len(),
            running_containers: containers.len(),
            isolated_containers: isolated_count,
            total_links: links.values().map(|targets| targets.len()).sum(),
            total_messages: history.len(),
            message_counts: counts.clone(),
        };
        println!("Orchestrator: ステータスサマリー = {status:?}");
        status
    }

    pub async fn add_container_with_builder(
        &self,
        mut builder: Builder,
        language: &str,
        source_file: &str,
        args: Vec<String>
    ) -> Result<Container> {
        println!("Orchestrator: コンテナ追加開始 (language={language}, source={source_file})");
        
        // ソースファイル名からコンテナ名を抽出（拡張子を除く）
        let container_name = std::path::Path::new(source_file)
            .file_stem()
            .and_then(|s| s.to_str())
            .unwrap_or("unknown")
            .to_string();
        
        // コンテナ名をIDとして設定
        builder = builder.with_id(&container_name);
        
        let container = builder
            .build_for_language(language, source_file, args)?;
        let mut containers = self.containers.lock().await;
        containers.insert(container_name, container.clone());
        println!("Orchestrator: コンテナ追加完了 (id={})", container.id());
        Ok(container)
    }
}

impl Default for Orchestrator {
    fn default() -> Self {
        Self::new()
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