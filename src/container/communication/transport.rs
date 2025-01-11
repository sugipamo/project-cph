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

    pub async fn send(&self, _from: &str, to: &str, message: Message) -> Result<()> {
        let mut buffers = self.buffers.lock().await;
        buffers.entry(to.to_string())
            .or_insert_with(Vec::new)
            .push(message);
        Ok(())
    }

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
        if let Some(messages) = buffers.get_mut(id) {
            messages.pop()
        } else {
            None
        }
    }
}

impl Default for Network {
    fn default() -> Self {
        Self::new()
    }
} 