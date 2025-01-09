use serde::{Serialize, Deserialize};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum LifecycleEvent {
    Create,
    Start,
    Stop,
    Remove,
} 