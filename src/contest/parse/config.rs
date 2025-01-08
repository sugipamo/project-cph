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
    #[must_use = "この関数は新しいNodeインスタンスを返します"]
    pub const fn new(value: String) -> Self {
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

impl Default for Config {
    fn default() -> Self {
        Self::new()
    }
}

impl Config {
    #[must_use = "この関数は新しいConfigインスタンスを返します"]
    pub const fn new() -> Self {
        Self {
            commands: HashMap::new(),
        }
    }

    #[must_use = "この関数はノードの関係を表すHashMapを返します"]
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

    #[must_use = "この関数はエイリアスグラフとノードインデックスを返します"]
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

    #[must_use = "この関数は指定された名前のノードを返します"]
    pub fn get_node_by_name(&self, name: &str) -> Option<Node> {
        let nodes = self.build_node_relationships();
        nodes.get(name).cloned()
    }
}