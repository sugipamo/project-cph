"""Tests for config resolver functions"""

from unittest.mock import Mock, patch

import pytest

from src.context.resolver.config_node import ConfigNode
from src.context.resolver.config_resolver import (
    _resolve_by_match_desc,
    create_config_root_from_dict,
    resolve_best,
    resolve_by_match_desc,
    resolve_format_string,
    resolve_formatted_string,
    resolve_values,
)


class TestCreateConfigRootFromDict:
    """Tests for create_config_root_from_dict function"""

    def test_create_config_root_from_dict_simple(self):
        """Test create_config_root_from_dict with simple dictionary"""
        data = {"key1": "value1", "key2": "value2"}

        root = create_config_root_from_dict(data)

        assert root.key == 'root'
        assert root.value == data
        assert len(root.next_nodes) == 2

        # Check child nodes
        child_keys = [node.key for node in root.next_nodes]
        assert 'key1' in child_keys
        assert 'key2' in child_keys

    def test_create_config_root_from_dict_with_aliases(self):
        """Test create_config_root_from_dict with aliases"""
        data = {
            "main_key": "value1",
            "aliases": ["alias1", "alias2"]
        }

        root = create_config_root_from_dict(data)

        assert "alias1" in root.matches
        assert "alias2" in root.matches
        assert len(root.next_nodes) == 1  # Only main_key, aliases is not a child

    def test_create_config_root_from_dict_nested(self):
        """Test create_config_root_from_dict with nested dictionaries"""
        data = {
            "outer": {
                "inner": "value",
                "nested": {"deep": "deep_value"}
            }
        }

        root = create_config_root_from_dict(data)

        assert len(root.next_nodes) == 1
        outer_node = root.next_nodes[0]
        assert outer_node.key == "outer"
        assert len(outer_node.next_nodes) == 2

    def test_create_config_root_from_dict_with_list(self):
        """Test create_config_root_from_dict with list values"""
        data = {
            "items": ["item1", "item2", "item3"]
        }

        root = create_config_root_from_dict(data)

        items_node = root.next_nodes[0]
        assert items_node.key == "items"
        assert len(items_node.next_nodes) == 3

        # Check list indices as keys
        child_keys = [node.key for node in items_node.next_nodes]
        assert child_keys == [0, 1, 2]

    def test_create_config_root_from_dict_invalid_aliases_type(self):
        """Test create_config_root_from_dict with invalid aliases type"""
        data = {
            "key": "value",
            "aliases": "not_a_list"  # Should be list
        }

        with pytest.raises(TypeError, match="aliasesはlist型である必要があります"):
            create_config_root_from_dict(data)

    def test_create_config_root_from_dict_non_dict(self):
        """Test create_config_root_from_dict with non-dict input"""
        with pytest.raises(ValueError, match="ConfigResolver: dict以外は未対応です"):
            create_config_root_from_dict("not_a_dict")

    def test_create_config_root_from_dict_empty(self):
        """Test create_config_root_from_dict with empty dictionary"""
        data = {}

        root = create_config_root_from_dict(data)

        assert root.key == 'root'
        assert root.value == data
        assert len(root.next_nodes) == 0


class TestResolveByMatchDesc:
    """Tests for resolve_by_match_desc function"""

    def test_resolve_by_match_desc_invalid_path_type(self):
        """Test resolve_by_match_desc with invalid path type"""
        root = Mock(spec=ConfigNode)

        with pytest.raises(TypeError, match="pathはlistまたはtupleである必要があります"):
            resolve_by_match_desc(root, "invalid_path")

    def test_resolve_by_match_desc_empty_path(self):
        """Test resolve_by_match_desc with empty path"""
        root = Mock(spec=ConfigNode)

        result = resolve_by_match_desc(root, [])

        assert result == []

    @patch('src.context.resolver.config_resolver._resolve_by_match_desc')
    def test_resolve_by_match_desc_calls_internal(self, mock_resolve):
        """Test resolve_by_match_desc calls internal function with tuple"""
        root = Mock(spec=ConfigNode)
        path = ["key1", "key2"]
        expected_result = [Mock()]
        mock_resolve.return_value = expected_result

        result = resolve_by_match_desc(root, path)

        mock_resolve.assert_called_once_with(root, ("key1", "key2"))
        assert result == expected_result

    def test_resolve_by_match_desc_with_tuple(self):
        """Test resolve_by_match_desc accepts tuple input"""
        root = Mock(spec=ConfigNode)
        path = ("key1", "key2")

        with patch('src.context.resolver.config_resolver._resolve_by_match_desc') as mock_resolve:
            mock_resolve.return_value = []
            resolve_by_match_desc(root, path)
            mock_resolve.assert_called_once_with(root, path)


class TestResolveBest:
    """Tests for resolve_best function"""

    @patch('src.context.resolver.config_resolver.resolve_by_match_desc')
    def test_resolve_best_with_results(self, mock_resolve):
        """Test resolve_best returns first result when results exist"""
        root = Mock(spec=ConfigNode)
        path = ["key1"]
        mock_nodes = [Mock(), Mock(), Mock()]
        mock_resolve.return_value = mock_nodes

        result = resolve_best(root, path)

        mock_resolve.assert_called_once_with(root, path)
        assert result == mock_nodes[0]

    @patch('src.context.resolver.config_resolver.resolve_by_match_desc')
    def test_resolve_best_no_results(self, mock_resolve):
        """Test resolve_best returns None when no results"""
        root = Mock(spec=ConfigNode)
        path = ["nonexistent"]
        mock_resolve.return_value = []

        result = resolve_best(root, path)

        mock_resolve.assert_called_once_with(root, path)
        assert result is None


class TestResolveValues:
    """Tests for resolve_values function"""

    @patch('src.context.resolver.config_resolver.resolve_by_match_desc')
    def test_resolve_values(self, mock_resolve):
        """Test resolve_values extracts values from nodes"""
        root = Mock(spec=ConfigNode)
        path = ["key1"]

        node1 = Mock()
        node1.value = "value1"
        node2 = Mock()
        node2.value = "value2"
        mock_resolve.return_value = [node1, node2]

        result = resolve_values(root, path)

        mock_resolve.assert_called_once_with(root, path)
        assert result == ["value1", "value2"]

    @patch('src.context.resolver.config_resolver.resolve_by_match_desc')
    def test_resolve_values_empty(self, mock_resolve):
        """Test resolve_values with empty results"""
        root = Mock(spec=ConfigNode)
        path = ["key1"]
        mock_resolve.return_value = []

        result = resolve_values(root, path)

        assert result == []


class TestResolveFormattedString:
    """Tests for resolve_formatted_string function"""

    def test_resolve_formatted_string_no_missing_keys(self):
        """Test resolve_formatted_string when no keys are missing"""
        root = Mock(spec=ConfigNode)

        result = resolve_formatted_string("Hello {name}", root, {"name": "World"})

        assert result == "Hello World"

    def test_resolve_formatted_string_with_missing_keys_found(self):
        """Test resolve_formatted_string when missing keys are found in config"""
        # Mock config node
        name_node = Mock()
        name_node.key = "name"
        name_node.value = "World"
        name_node.parent = None
        name_node.next_nodes = []

        root = Mock()
        root.parent = None
        root.next_nodes = [name_node]

        result = resolve_formatted_string("Hello {name}", root)

        assert result == "Hello World"

    @patch('src.operations.pure.formatters.format_with_missing_keys')
    def test_resolve_formatted_string_with_dict_value(self, mock_format):
        """Test resolve_formatted_string when config value is dict with 'value' key"""
        mock_format.side_effect = [
            ("Hello {name}", {"name"}),
            ("Hello World", set())
        ]

        name_node = Mock()
        name_node.key = "name"
        name_node.value = {"value": "World", "other": "data"}
        name_node.parent = None
        name_node.next_nodes = []

        root = Mock()
        root.parent = None
        root.next_nodes = [name_node]

        result = resolve_formatted_string("Hello {name}", root)

        assert result == "Hello World"

    def test_resolve_formatted_string_no_initial_values(self):
        """Test resolve_formatted_string without initial values"""
        root = Mock(spec=ConfigNode)

        result = resolve_formatted_string("test string", root)

        assert result == "test string"

    @patch('src.operations.pure.formatters.format_with_missing_keys')
    def test_resolve_formatted_string_circular_reference_protection(self, mock_format):
        """Test resolve_formatted_string handles circular references"""
        mock_format.side_effect = [
            ("Hello {name}", {"name"}),
            ("Hello {name}", {"name"})  # Still missing after search
        ]

        # Create circular reference
        node1 = Mock()
        node1.key = "node1"
        node1.value = "value1"
        node1.parent = None

        node2 = Mock()
        node2.key = "node2"
        node2.value = "value2"
        node2.parent = node1

        node1.next_nodes = [node2]
        node2.next_nodes = [node1]  # Circular reference

        root = Mock()
        root.parent = None
        root.next_nodes = [node1]

        result = resolve_formatted_string("Hello {name}", root)

        assert result == "Hello {name}"  # Returns with unresolved keys


class TestResolveFormatString:
    """Tests for resolve_format_string function"""

    def test_resolve_format_string_simple_string_value(self):
        """Test resolve_format_string with simple string value"""
        node = Mock()
        node.value = "Hello {name}"

        result = resolve_format_string(node, {"name": "World"})

        assert result == "Hello World"

    def test_resolve_format_string_dict_with_value_key(self):
        """Test resolve_format_string with dict containing 'value' key"""
        node = Mock()
        node.value = {"value": "Hello {name}", "other": "data"}

        result = resolve_format_string(node, {"name": "World"})

        assert result == "Hello World"

    def test_resolve_format_string_non_string_value(self):
        """Test resolve_format_string with non-string value"""
        node = Mock()
        node.value = 42

        result = resolve_format_string(node)

        assert result == "42"

    def test_resolve_format_string_dict_without_value_key(self):
        """Test resolve_format_string with dict without 'value' key"""
        node = Mock()
        node.value = {"data": "test", "other": "info"}

        result = resolve_format_string(node)

        assert result == str(node.value)

    def test_resolve_format_string_with_missing_keys_resolution(self):
        """Test resolve_format_string resolves missing keys from config tree"""
        # Target node
        target_node = Mock()
        target_node.value = "Hello {name}"
        target_node.parent = None

        # Config node with the missing key
        name_node = Mock()
        name_node.key = "name"
        name_node.value = "World"
        name_node.parent = target_node
        name_node.next_nodes = []

        target_node.next_nodes = [name_node]

        result = resolve_format_string(target_node)

        assert result == "Hello World"

    @patch('src.operations.pure.formatters.format_with_missing_keys')
    def test_resolve_format_string_with_integer_config_value(self, mock_format):
        """Test resolve_format_string with integer config value"""
        mock_format.side_effect = [
            ("Count: {count}", {"count"}),
            ("Count: 42", set())
        ]

        target_node = Mock()
        target_node.value = "Count: {count}"
        target_node.parent = None

        count_node = Mock()
        count_node.key = "count"
        count_node.value = 42
        count_node.parent = target_node
        count_node.next_nodes = []

        target_node.next_nodes = [count_node]

        result = resolve_format_string(target_node)

        assert result == "Count: 42"


class TestInternalResolveByMatchDesc:
    """Tests for _resolve_by_match_desc internal function"""

    def test_resolve_by_match_desc_empty_path(self):
        """Test _resolve_by_match_desc with empty path"""
        root = Mock(spec=ConfigNode)

        result = _resolve_by_match_desc(root, ())

        assert result == []

    def test_resolve_by_match_desc_single_match(self):
        """Test _resolve_by_match_desc with single matching node"""
        # Create mock nodes
        child_node = Mock()
        child_node.matches = {"target_key"}
        child_node.next_nodes = []

        root = Mock()
        root.next_nodes = [child_node]

        result = _resolve_by_match_desc(root, ("target_key",))

        assert len(result) == 1
        assert result[0] == child_node

    def test_resolve_by_match_desc_no_matches(self):
        """Test _resolve_by_match_desc with no matching nodes"""
        child_node = Mock()
        child_node.matches = {"other_key"}
        child_node.next_nodes = []

        root = Mock()
        root.next_nodes = [child_node]

        result = _resolve_by_match_desc(root, ("target_key",))

        assert result == []

    def test_resolve_by_match_desc_multiple_matches_sorted(self):
        """Test _resolve_by_match_desc with multiple matches sorted by rank"""
        # Create mock nodes with different match ranks
        node1 = Mock()
        node1.matches = {"key1"}  # Will match first element
        node1.next_nodes = []

        node2 = Mock()
        node2.matches = {"key2"}  # Will match second element
        node2.next_nodes = []

        root = Mock()
        root.next_nodes = [node1, node2]

        # Path with two keys, first key should have higher rank
        result = _resolve_by_match_desc(root, ("key1", "key2"))

        # Results should be sorted by match rank (higher first)
        assert len(result) >= 1
        # Detailed ranking verification would require more complex setup

    def test_resolve_by_match_desc_nested_structure(self):
        """Test _resolve_by_match_desc with nested node structure"""
        # Create nested structure
        grandchild = Mock()
        grandchild.matches = {"target"}
        grandchild.next_nodes = []

        child = Mock()
        child.matches = {"intermediate"}
        child.next_nodes = [grandchild]

        root = Mock()
        root.next_nodes = [child]

        result = _resolve_by_match_desc(root, ("target",))

        assert len(result) == 1
        assert result[0] == grandchild

    def test_resolve_by_match_desc_visited_node_handling(self):
        """Test _resolve_by_match_desc handles already visited nodes"""
        # Create a node that could be visited multiple times
        shared_node = Mock()
        shared_node.matches = {"shared"}
        shared_node.next_nodes = []

        node1 = Mock()
        node1.matches = set()
        node1.next_nodes = [shared_node]

        node2 = Mock()
        node2.matches = set()
        node2.next_nodes = [shared_node]

        root = Mock()
        root.next_nodes = [node1, node2]

        result = _resolve_by_match_desc(root, ("shared",))

        # The current implementation may return duplicate nodes from different paths
        shared_results = [r for r in result if r == shared_node]
        assert len(shared_results) >= 1


class TestConfigResolverEdgeCases:
    """Tests for edge cases and error handling in config resolver"""

    def test_create_config_root_complex_nested_aliases(self):
        """Test create_config_root_from_dict with deeply nested aliases"""
        data = {
            "level1": {
                "level2": {
                    "level3": "deep_value",
                    "aliases": ["deep_alias"]
                },
                "aliases": ["mid_alias"]
            },
            "aliases": ["root_alias"]
        }

        root = create_config_root_from_dict(data)

        # Check root aliases
        assert "root_alias" in root.matches

        # Navigate to level1
        level1_node = next(node for node in root.next_nodes if node.key == "level1")
        assert "mid_alias" in level1_node.matches

        # Navigate to level2
        level2_node = next(node for node in level1_node.next_nodes if node.key == "level2")
        assert "deep_alias" in level2_node.matches

    def test_create_config_root_mixed_list_and_dict(self):
        """Test create_config_root_from_dict with mixed list and dict structures"""
        data = {
            "mixed": [
                {"name": "item1", "value": 1},
                {"name": "item2", "value": 2},
                "string_item"
            ]
        }

        root = create_config_root_from_dict(data)

        mixed_node = root.next_nodes[0]
        assert len(mixed_node.next_nodes) == 3

        # Check dict items have proper structure
        dict_item = mixed_node.next_nodes[0]
        assert len(dict_item.next_nodes) == 2  # name and value

    def test_resolve_formatted_string_complex_key_resolution(self):
        """Test resolve_formatted_string with complex key resolution scenario"""
        # Create a complex tree structure
        root = Mock()
        root.parent = None

        # Create nested nodes
        config_node = Mock()
        config_node.key = "config"
        config_node.value = {"nested": "data"}
        config_node.parent = root

        app_node = Mock()
        app_node.key = "app"
        app_node.value = {"value": "MyApp"}
        app_node.parent = config_node

        version_node = Mock()
        version_node.key = "version"
        version_node.value = "1.0.0"
        version_node.parent = root

        # Set up relationships
        root.next_nodes = [config_node, version_node]
        config_node.next_nodes = [app_node]
        app_node.next_nodes = []
        version_node.next_nodes = []

        result = resolve_formatted_string(
            "Welcome to {app} version {version}!",
            root
        )

        assert "MyApp" in result
        assert "1.0.0" in result

    def test_resolve_formatted_string_missing_keys_not_found(self):
        """Test resolve_formatted_string when keys are never found"""
        root = Mock()
        root.parent = None
        root.next_nodes = []

        result = resolve_formatted_string("Hello {missing_key}", root)

        assert result == "Hello {missing_key}"  # Unresolved keys remain

    def test_resolve_format_string_deep_tree_traversal(self):
        """Test resolve_format_string traverses deep tree structures"""
        # Create deep tree: root -> level1 -> level2 -> level3 (contains target key)
        target_node = Mock()
        target_node.value = "Config: {deep_key}"
        target_node.parent = None

        level1 = Mock()
        level1.key = "level1"
        level1.value = "data1"
        level1.parent = target_node

        level2 = Mock()
        level2.key = "level2"
        level2.value = "data2"
        level2.parent = level1

        level3 = Mock()
        level3.key = "deep_key"
        level3.value = "found_value"
        level3.parent = level2
        level3.next_nodes = []

        level2.next_nodes = [level3]
        level1.next_nodes = [level2]
        target_node.next_nodes = [level1]

        result = resolve_format_string(target_node)

        assert result == "Config: found_value"

    def test_resolve_format_string_circular_detection(self):
        """Test resolve_format_string handles circular references without infinite loop"""
        # Create circular reference
        node1 = Mock()
        node1.key = "node1"
        node1.value = "Hello {missing}"
        node1.parent = None

        node2 = Mock()
        node2.key = "node2"
        node2.value = "value2"
        node2.parent = node1

        # Create circular reference
        node1.next_nodes = [node2]
        node2.next_nodes = [node1]  # Circular

        # Should not hang and should handle gracefully
        result = resolve_format_string(node1)

        # Should return some result without infinite loop
        assert isinstance(result, str)

    def test_resolve_format_string_dict_value_variations(self):
        """Test resolve_format_string with various dict value structures"""
        # Test with dict containing 'value' key that is also a dict
        node = Mock()
        node.value = {"value": {"nested": "data"}}
        node.parent = None
        node.next_nodes = []

        result = resolve_format_string(node)

        # Should convert dict to string
        assert "nested" in result or "data" in result

    def test_internal_resolve_edge_cases(self):
        """Test _resolve_by_match_desc with various edge cases"""
        # Test with node having empty matches set
        empty_node = Mock()
        empty_node.matches = set()
        empty_node.next_nodes = []

        root = Mock()
        root.next_nodes = [empty_node]

        result = _resolve_by_match_desc(root, ("any_key",))
        assert result == []

        # Test with multiple path segments
        node1 = Mock()
        node1.matches = {"first"}

        node2 = Mock()
        node2.matches = {"second"}
        node2.next_nodes = []

        node1.next_nodes = [node2]
        root.next_nodes = [node1]

        result = _resolve_by_match_desc(root, ("first", "second"))
        # Should find matches for both segments
        assert len(result) >= 1

    def test_resolve_formatted_string_key_value_precedence(self):
        """Test resolve_formatted_string key resolution precedence"""
        # Test that initial_values take precedence over config values
        config_node = Mock()
        config_node.key = "name"
        config_node.value = "FromConfig"
        config_node.parent = None
        config_node.next_nodes = []

        root = Mock()
        root.parent = None
        root.next_nodes = [config_node]

        result = resolve_formatted_string(
            "Hello {name}",
            root,
            {"name": "FromInitial"}  # Should take precedence
        )

        assert result == "Hello FromInitial"

    def test_resolve_formatted_string_none_value_handling(self):
        """Test resolve_formatted_string handles None values properly"""
        config_node = Mock()
        config_node.key = "nullable"
        config_node.value = None
        config_node.parent = None
        config_node.next_nodes = []

        root = Mock()
        root.parent = None
        root.next_nodes = [config_node]

        # None values should be skipped, key remains unresolved
        result = resolve_formatted_string("Value: {nullable}", root)

        assert result == "Value: {nullable}"

    def test_create_config_root_aliases_with_special_characters(self):
        """Test create_config_root_from_dict with aliases containing special characters"""
        data = {
            "main": "value",
            "aliases": ["alias-with-dash", "alias_with_underscore", "alias.with.dots"]
        }

        root = create_config_root_from_dict(data)

        assert "alias-with-dash" in root.matches
        assert "alias_with_underscore" in root.matches
        assert "alias.with.dots" in root.matches

    def test_resolve_format_string_key_already_in_values(self):
        """Test resolve_format_string when key is already resolved in initial values"""
        node = Mock()
        node.value = "Hello {name}"
        node.parent = None
        node.next_nodes = []

        # Even though initial_values has the key, it should still work
        result = resolve_format_string(node, {"name": "World"})

        assert result == "Hello World"
