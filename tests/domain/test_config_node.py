import pytest
from src.domain.config_node import ConfigNode


class TestConfigNode:
    def test_init_basic(self):
        node = ConfigNode("test_key", {"value": 123})
        assert node.key == "test_key"
        assert node.value == {"value": 123}
        assert node.parent is None
        assert node.matches == {"test_key", "*"}
        assert node.next_nodes == []

    def test_add_edge(self):
        parent = ConfigNode("parent", {})
        child = ConfigNode("child", {"data": "test"})
        
        parent.add_edge(child)
        
        assert child.parent == parent
        assert child in parent.next_nodes
        assert child.key == "child"
        assert child.value == {"data": "test"}

    def test_add_edge_duplicate(self):
        parent = ConfigNode("parent", {})
        child = ConfigNode("child", {})
        
        parent.add_edge(child)
        
        with pytest.raises(ValueError, match="重複したエッジは許可されていません"):
            parent.add_edge(child)

    def test_repr(self):
        node = ConfigNode("test_key", {"value": 123})
        # Check that repr contains expected parts
        repr_str = repr(node)
        assert "key='test_key'" in repr_str
        assert "value={'value': 123}" in repr_str
        assert "'test_key'" in repr_str
        assert "'*'" in repr_str
        assert "next_nodes=[]" in repr_str

    def test_repr_with_next_nodes(self):
        parent = ConfigNode("parent", {})
        child1 = ConfigNode("child1", {})
        child2 = ConfigNode("child2", {})
        
        parent.add_edge(child1)
        parent.add_edge(child2)
        
        assert "next_nodes=['child1', 'child2']" in repr(parent)

    def test_next_nodes_with_key(self):
        parent = ConfigNode("parent", {})
        child1 = ConfigNode("child1", {})
        child2 = ConfigNode("child2", {})
        child3 = ConfigNode("special", {})
        
        parent.add_edge(child1)
        parent.add_edge(child2)
        parent.add_edge(child3)
        
        # Test finding by exact key
        results = parent.next_nodes_with_key("child1")
        assert len(results) == 1
        assert results[0] == child1
        
        # Test wildcard match - '*' needs to be the search key
        results = parent.next_nodes_with_key("*")
        assert len(results) == 3  # All nodes match due to '*' in matches
        
        # Test no match
        results = parent.next_nodes_with_key("nonexistent")
        assert len(results) == 0

    def test_path(self):
        root = ConfigNode("root", {})
        level1 = ConfigNode("level1", {})
        level2 = ConfigNode("level2", {})
        
        root.add_edge(level1)
        level1.add_edge(level2)
        
        assert root.path() == []
        assert level1.path() == ["level1"]
        assert level2.path() == ["level1", "level2"]

    def test_find_nearest_key_node(self):
        root = ConfigNode("root", {})
        branch1 = ConfigNode("branch1", {})
        branch2 = ConfigNode("branch2", {})
        target = ConfigNode("target", {})
        
        root.add_edge(branch1)
        root.add_edge(branch2)
        branch2.add_edge(target)
        
        # Find from root
        results = root.find_nearest_key_node("target")
        assert len(results) == 1
        assert results[0] == target
        
        # Find from branch1 (shouldn't find anything)
        results = branch1.find_nearest_key_node("nonexistent")
        assert len(results) == 0

    def test_value_none(self):
        node = ConfigNode("key", None)
        assert node.key == "key"
        assert node.value is None
        assert node.matches == {"key", "*"}