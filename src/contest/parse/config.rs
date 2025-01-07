use serde::{Deserialize, Serialize};
use std::collections::HashMap;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Config {
    pub commands: HashMap<String, HashMap<String, CommandValue>>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(untagged)]
pub enum CommandValue {
    Command { aliases: Vec<String> },
    Setting { priority: i32 },
}

impl Config {
    pub fn new() -> Self {
        Self {
            commands: HashMap::new(),
        }
    }
}