use super::protocol::Message;
use anyhow::Result;
use std::collections::HashMap;
use std::sync::Arc;
use tokio::sync::Mutex;

pub struct Network {
    buffers: Arc<Mutex<HashMap<String, Vec<Message>>>>,
}

impl Network {
    pub fn new() -> Self {
        Self {
            buffers: Arc::new(Mutex::new(HashMap::new())),
        }
    }

    /// メッセージを指定された宛先に送信します。
    /// 
    /// # Errors
    /// 
    /// - メッセージの送信に失敗した場合にエラーを返します。
    pub async fn send(&self, _from: &str, to: &str, message: Message) -> Result<()> {
        let mut buffers = self.buffers.lock().await;
        buffers.entry(to.to_string())
            .or_insert_with(Vec::new)
            .push(message);
        Ok(())
    }

    /// メッセージを全ての宛先（送信者以外）にブロードキャストします。
    /// 
    /// # Errors
    /// 
    /// - メッセージの送信に失敗した場合にエラーを返します。
    pub async fn broadcast(&self, from: &str, message: Message) -> Result<()> {
        let mut buffers = self.buffers.lock().await;
        let recipients: Vec<String> = buffers.keys()
            .filter(|id| *id != from)
            .cloned()
            .collect();
        
        for id in recipients {
            buffers.entry(id)
                .or_insert_with(Vec::new)
                .push(message.clone());
        }
        Ok(())
    }

    pub async fn receive(&self, id: &str) -> Option<Message> {
        let mut buffers = self.buffers.lock().await;
        buffers.get_mut(id).and_then(|messages| messages.pop())
    }
}

impl Default for Network {
    fn default() -> Self {
        Self::new()
    }
} 