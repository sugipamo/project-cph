import pytest
from src.domain.config_node import ConfigNode
from src.domain.config_node_service import init_matches, add_edge, path


class TestConfigNodeLogic:
    def test_init_matches_with_aliases(self):
        node = ConfigNode("test", {})
        value = {"aliases": ["alias1", "alias2"], "other": "data"}
        
        init_matches(node, value)
        
        assert node.matches == {"test", "*", "alias1", "alias2"}
        assert node.value == {"other": "data"}
        assert "aliases" not in node.value

    def test_init_matches_without_aliases(self):
        node = ConfigNode("test", {})
        value = {"key": "value", "other": "data"}
        
        init_matches(node, value)
        
        assert node.matches == {"test", "*"}
        assert node.value == {"key": "value", "other": "data"}

    def test_init_matches_invalid_aliases_type(self):
        node = ConfigNode("test", {})
        value = {"aliases": "not_a_list"}
        
        with pytest.raises(TypeError, match="aliasesはlist型である必要があります"):
            init_matches(node, value)

    def test_init_matches_non_dict_value(self):
        node = ConfigNode("test", {})
        value = "simple_string"
        
        init_matches(node, value)
        
        assert node.value == "simple_string"
        assert node.matches == {"test", "*"}

    def test_add_edge_success(self):
        parent = ConfigNode("parent", {})
        child = ConfigNode("child", {})
        
        add_edge(parent, child)
        
        assert child in parent.next_nodes
        assert child.parent == parent

    def test_add_edge_duplicate_raises_error(self):
        parent = ConfigNode("parent", {})
        child = ConfigNode("child", {})
        
        add_edge(parent, child)
        
        with pytest.raises(ValueError, match="重複したエッジは許可されていません"):
            add_edge(parent, child)

    def test_path_single_node(self):
        node = ConfigNode("root", {})
        
        result = path(node)
        
        assert result == []

    def test_path_two_levels(self):
        parent = ConfigNode("parent", {})
        child = ConfigNode("child", {})
        add_edge(parent, child)
        
        result = path(child)
        
        assert result == ["child"]

    def test_path_three_levels(self):
        grandparent = ConfigNode("grandparent", {})
        parent = ConfigNode("parent", {})
        child = ConfigNode("child", {})
        
        add_edge(grandparent, parent)
        add_edge(parent, child)
        
        result = path(child)
        
        assert result == ["parent", "child"]

    def test_path_deep_hierarchy(self):
        root = ConfigNode("root", {})
        level1 = ConfigNode("level1", {})
        level2 = ConfigNode("level2", {})
        level3 = ConfigNode("level3", {})
        level4 = ConfigNode("level4", {})
        
        add_edge(root, level1)
        add_edge(level1, level2)
        add_edge(level2, level3)
        add_edge(level3, level4)
        
        result = path(level4)
        
        assert result == ["level1", "level2", "level3", "level4"]

    def test_init_matches_with_empty_aliases(self):
        node = ConfigNode("test", {})
        value = {"aliases": [], "data": "value"}
        
        init_matches(node, value)
        
        assert node.matches == {"test", "*"}
        assert node.value == {"data": "value"}

    def test_init_matches_preserves_existing_matches(self):
        node = ConfigNode("test", {})
        node.matches.add("existing")
        value = {"aliases": ["new1", "new2"]}
        
        init_matches(node, value)
        
        assert node.matches == {"test", "*", "existing", "new1", "new2"}

    def test_add_edge_updates_parent_correctly(self):
        parent1 = ConfigNode("parent1", {})
        parent2 = ConfigNode("parent2", {})
        child = ConfigNode("child", {})
        
        # First add to parent1
        add_edge(parent1, child)
        assert child.parent == parent1
        assert child in parent1.next_nodes
        
        # Now add to parent2
        add_edge(parent2, child)
        assert child.parent == parent2
        assert child in parent2.next_nodes
        assert child in parent1.next_nodes  # Still in parent1's list