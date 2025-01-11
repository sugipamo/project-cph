use serde::{Serialize, Deserialize};
use chrono::{DateTime, Utc};
use crate::container::state::lifecycle::ContainerStatus;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum Message {
    Data(#[serde(with = "serde_bytes")] Vec<u8>),
    Control(ControlMessage),
    Status(StatusMessage),
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum ControlMessage {
    Start,
    Stop,
    Pause,
    Resume,
    Custom(String, #[serde(with = "serde_bytes")] Vec<u8>),
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct StatusMessage {
    pub container_id: String,
    pub status: ContainerStatus,
    #[serde(with = "chrono::serde::ts_seconds")]
    pub timestamp: DateTime<Utc>,
} 