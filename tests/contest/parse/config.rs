#[cfg(test)]
mod tests {
    use cph::contest::parse::{Config, CommandValue};
    use std::collections::HashMap;

    #[test]
    fn test_new_config() {
        let config = Config::new();
        assert!(config.commands.is_empty());
    }

    #[test]
    fn test_build_node_relationships() {
        let mut config = Config::new();
        let mut commands = HashMap::new();
        let mut site_commands = HashMap::new();
        
        site_commands.insert(
            "atcoder".to_string(),
            CommandValue::Command {
                aliases: vec!["at".to_string(), "a".to_string()],
            },
        );
        
        commands.insert("site".to_string(), site_commands);
        config.commands = commands;

        let nodes = config.build_node_relationships();
        
        // ルートノードの確認
        assert!(nodes.contains_key("site"));
        
        // サイトノードの確認
        let atcoder_node = nodes.get("atcoder").expect("atcoderノードが存在しません");
        assert_eq!(atcoder_node.parent, Some("site".to_string()));
        assert!(atcoder_node.children.contains(&"at".to_string()));
        assert!(atcoder_node.children.contains(&"a".to_string()));
        
        // エイリアスノードの確認
        let at_node = nodes.get("at").expect("atノードが存在しません");
        assert_eq!(at_node.parent, Some("atcoder".to_string()));
        assert!(at_node.children.is_empty());
    }

    #[test]
    fn test_build_alias_graph() {
        let mut config = Config::new();
        let mut commands = HashMap::new();
        let mut site_commands = HashMap::new();
        
        site_commands.insert(
            "codeforces".to_string(),
            CommandValue::Command {
                aliases: vec!["cf".to_string()],
            },
        );
        
        commands.insert("site".to_string(), site_commands);
        config.commands = commands;

        let (graph, node_indices) = config.build_alias_graph();
        
        // ノード数の確認
        assert_eq!(graph.node_count(), 3); // site, codeforces, cf
        assert_eq!(node_indices.len(), 3);
        
        // エッジの確認
        assert_eq!(graph.edge_count(), 2); // site->codeforces, codeforces->cf
    }

    #[test]
    fn test_get_node_by_name() {
        let mut config = Config::new();
        let mut commands = HashMap::new();
        let mut site_commands = HashMap::new();
        
        site_commands.insert(
            "yukicoder".to_string(),
            CommandValue::Command {
                aliases: vec!["yk".to_string()],
            },
        );
        
        commands.insert("site".to_string(), site_commands);
        config.commands = commands;

        // 存在するノードの確認
        let node = config.get_node_by_name("yukicoder");
        assert!(node.is_some());
        let node = node.unwrap();
        assert_eq!(node.value, "yukicoder");
        assert_eq!(node.parent, Some("site".to_string()));
        
        // 存在しないノードの確認
        let node = config.get_node_by_name("nonexistent");
        assert!(node.is_none());
    }
} 