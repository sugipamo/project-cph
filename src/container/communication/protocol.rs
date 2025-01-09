use bytes::Bytes;
use serde::{Serialize, Deserialize};
use chrono::{DateTime, Utc};
use crate::container::state::lifecycle::ContainerStatus;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum Message {
    Data(Bytes),
    Control(ControlMessage),
    Status(StatusMessage),
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum ControlMessage {
    Start,
    Stop,
    Pause,
    Resume,
    Custom(String, Bytes),
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct StatusMessage {
    pub container_id: String,
    pub status: ContainerStatus,
    pub timestamp: DateTime<Utc>,
} 