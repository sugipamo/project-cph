use serde::{Deserialize, Serialize};
use std::collections::HashMap;
use petgraph::graph::{DiGraph, NodeIndex};
use petgraph::Direction;

#[derive(Debug, Clone)]
pub struct Node {
    pub value: String,
    pub parent: Option<String>,
    pub children: Vec<String>,
    pub category: Option<String>,
}

impl Node {
    pub fn new(value: String) -> Self {
        Self {
            value,
            parent: None,
            children: Vec::new(),
            category: None,
        }
    }
}

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

    pub fn build_node_relationships(&self) -> HashMap<String, Node> {
        let (graph, node_indices) = self.build_alias_graph();
        let mut nodes = HashMap::new();

        // 全ノードの初期化
        for (name, _) in &node_indices {
            nodes.insert(name.clone(), Node::new(name.clone()));
        }

        // 親子関係の構築
        for (name, idx) in &node_indices {
            let mut parents = graph.neighbors_directed(*idx, Direction::Incoming);
            if let Some(parent_idx) = parents.next() {
                let parent_name = &graph[parent_idx];
                
                // 親の設定
                if let Some(node) = nodes.get_mut(name) {
                    node.parent = Some(parent_name.clone());
                }
                
                // 子の設定
                if let Some(parent_node) = nodes.get_mut(parent_name) {
                    parent_node.children.push(name.clone());
                }

                // カテゴリーの設定
                let mut category_parents = graph.neighbors_directed(parent_idx, Direction::Incoming);
                if let Some(category_idx) = category_parents.next() {
                    let category_name = &graph[category_idx];
                    if let Some(node) = nodes.get_mut(name) {
                        node.category = Some(category_name.clone());
                    }
                }
            }
        }

        nodes
    }

    pub fn build_alias_graph(&self) -> (DiGraph<String, ()>, HashMap<String, NodeIndex>) {
        let mut graph = DiGraph::new();
        let mut node_indices = HashMap::new();

        // グラフの構築
        for (category, subcmds) in &self.commands {
            let category_idx = *node_indices
                .entry(category.clone())
                .or_insert_with(|| graph.add_node(category.clone()));

            for (subcmd, value) in subcmds {
                let subcmd_idx = *node_indices
                    .entry(subcmd.clone())
                    .or_insert_with(|| graph.add_node(subcmd.clone()));
                graph.add_edge(category_idx, subcmd_idx, ());

                if let CommandValue::Command { aliases } = value {
                    for alias in aliases {
                        let alias_idx = *node_indices
                            .entry(alias.clone())
                            .or_insert_with(|| graph.add_node(alias.clone()));
                        graph.add_edge(subcmd_idx, alias_idx, ());
                    }
                }
            }
        }

        (graph, node_indices)
    }

    pub fn get_node_by_name(&self, name: &str) -> Option<Node> {
        let nodes = self.build_node_relationships();
        nodes.get(name).cloned()
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    fn create_test_config() -> Config {
        let mut config = Config::new();
        let mut executions = HashMap::new();
        let mut settings = HashMap::new();

        // executions の設定
        executions.insert(
            "test".to_string(),
            CommandValue::Command {
                aliases: vec!["t".to_string(), "check".to_string()],
            },
        );

        // settings の設定
        settings.insert(
            "site".to_string(),
            CommandValue::Command {
                aliases: vec!["ac".to_string(), "at-coder".to_string()],
            },
        );

        config.commands.insert("executions".to_string(), executions);
        config.commands.insert("settings".to_string(), settings);
        config
    }

    #[test]
    fn test_node_relationships() {
        let config = create_test_config();
        
        // エイリアスからノードを取得
        let ac_node = config.get_node_by_name("ac").unwrap();
        assert_eq!(ac_node.value, "ac");
        assert_eq!(ac_node.parent.unwrap(), "site");
        assert!(ac_node.children.is_empty());
        assert_eq!(ac_node.category.unwrap(), "settings");

        // 親コマンドからノードを取得
        let site_node = config.get_node_by_name("site").unwrap();
        assert_eq!(site_node.value, "site");
        assert_eq!(site_node.parent.unwrap(), "settings");
        assert!(site_node.children.contains(&"ac".to_string()));
        assert!(site_node.children.contains(&"at-coder".to_string()));

        // executions カテゴリのテスト
        let test_node = config.get_node_by_name("test").unwrap();
        assert_eq!(test_node.value, "test");
        assert_eq!(test_node.parent.unwrap(), "executions");
        assert!(test_node.children.contains(&"t".to_string()));
        assert!(test_node.children.contains(&"check".to_string()));
    }

    #[test]
    fn test_node_relationships_map() {
        let config = create_test_config();
        let nodes = config.build_node_relationships();

        // 全ノードの数を確認
        assert_eq!(nodes.len(), 8); // executions, settings, test, t, check, site, ac, at-coder

        // 特定のノードの親子関係を確認
        let test_node = nodes.get("test").unwrap();
        assert_eq!(test_node.children.len(), 2);
        assert_eq!(test_node.parent.as_ref().unwrap(), "executions");

        // エイリアスノードの確認
        let alias_node = nodes.get("t").unwrap();
        assert_eq!(alias_node.parent.as_ref().unwrap(), "test");
        assert!(alias_node.children.is_empty());
    }
}