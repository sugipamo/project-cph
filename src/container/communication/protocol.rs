use serde::{Deserialize, Serialize};
use std::fmt;
use crate::container::state::lifecycle::Status;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum Message {
    Control(ControlMessage),
    Status(StatusMessage),
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum ControlMessage {
    Start,
    Stop,
    Kill,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct StatusMessage {
    pub container_id: String,
    pub status: Status,
} 