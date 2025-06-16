"""Tests for data_processors utility functions"""
import pytest

from src.utils.data_processors import filter_and_transform_items, group_items_by_key, merge_dictionaries


class TestDataProcessors:
    """Test suite for data processing utility functions"""

    def test_filter_and_transform_items_empty_list(self):
        """Test filter_and_transform_items with empty list"""
        result = filter_and_transform_items([], lambda x: True, lambda x: x)
        assert result == []

    def test_filter_and_transform_items_all_pass(self):
        """Test filter_and_transform_items where all items pass filter"""
        items = [1, 2, 3, 4, 5]
        filter_func = lambda x: True
        transform_func = lambda x: x * 2

        result = filter_and_transform_items(items, filter_func, transform_func)
        assert result == [2, 4, 6, 8, 10]

    def test_filter_and_transform_items_none_pass(self):
        """Test filter_and_transform_items where no items pass filter"""
        items = [1, 2, 3, 4, 5]
        filter_func = lambda x: False
        transform_func = lambda x: x * 2

        result = filter_and_transform_items(items, filter_func, transform_func)
        assert result == []

    def test_filter_and_transform_items_some_pass(self):
        """Test filter_and_transform_items where some items pass filter"""
        items = [1, 2, 3, 4, 5]
        filter_func = lambda x: x % 2 == 0  # Even numbers only
        transform_func = lambda x: x * 2

        result = filter_and_transform_items(items, filter_func, transform_func)
        assert result == [4, 8]  # 2*2, 4*2

    def test_filter_and_transform_items_complex_objects(self):
        """Test filter_and_transform_items with complex objects"""
        items = [
            {"name": "Alice", "age": 25},
            {"name": "Bob", "age": 30},
            {"name": "Charlie", "age": 20}
        ]
        filter_func = lambda x: x["age"] >= 25
        transform_func = lambda x: x["name"].upper()

        result = filter_and_transform_items(items, filter_func, transform_func)
        assert result == ["ALICE", "BOB"]

    def test_group_items_by_key_empty_list(self):
        """Test group_items_by_key with empty list"""
        result = group_items_by_key([], lambda x: x)
        assert result == {}

    def test_group_items_by_key_simple_grouping(self):
        """Test group_items_by_key with simple grouping"""
        items = [1, 2, 3, 4, 5]
        key_func = lambda x: x % 2  # Group by even/odd

        result = group_items_by_key(items, key_func)
        assert result == {
            0: [2, 4],  # Even numbers
            1: [1, 3, 5]  # Odd numbers
        }

    def test_group_items_by_key_string_grouping(self):
        """Test group_items_by_key with string grouping"""
        items = ["apple", "banana", "apricot", "blueberry", "cherry"]
        key_func = lambda x: x[0]  # Group by first letter

        result = group_items_by_key(items, key_func)
        assert result == {
            'a': ["apple", "apricot"],
            'b': ["banana", "blueberry"],
            'c': ["cherry"]
        }

    def test_group_items_by_key_complex_objects(self):
        """Test group_items_by_key with complex objects"""
        items = [
            {"name": "Alice", "department": "Engineering"},
            {"name": "Bob", "department": "Marketing"},
            {"name": "Charlie", "department": "Engineering"},
            {"name": "Diana", "department": "Marketing"}
        ]
        key_func = lambda x: x["department"]

        result = group_items_by_key(items, key_func)
        assert len(result) == 2
        assert len(result["Engineering"]) == 2
        assert len(result["Marketing"]) == 2
        assert result["Engineering"][0]["name"] == "Alice"
        assert result["Engineering"][1]["name"] == "Charlie"

    def test_group_items_by_key_single_group(self):
        """Test group_items_by_key where all items belong to same group"""
        items = [1, 2, 3, 4, 5]
        key_func = lambda x: "same"

        result = group_items_by_key(items, key_func)
        assert result == {"same": [1, 2, 3, 4, 5]}

    def test_merge_dictionaries_empty(self):
        """Test merge_dictionaries with no dictionaries"""
        result = merge_dictionaries()
        assert result == {}

    def test_merge_dictionaries_single(self):
        """Test merge_dictionaries with single dictionary"""
        dict1 = {"a": 1, "b": 2}
        result = merge_dictionaries(dict1)
        assert result == {"a": 1, "b": 2}
        # Ensure original dict is not modified
        assert dict1 == {"a": 1, "b": 2}

    def test_merge_dictionaries_multiple_no_overlap(self):
        """Test merge_dictionaries with multiple dictionaries, no key overlap"""
        dict1 = {"a": 1, "b": 2}
        dict2 = {"c": 3, "d": 4}
        dict3 = {"e": 5}

        result = merge_dictionaries(dict1, dict2, dict3)
        assert result == {"a": 1, "b": 2, "c": 3, "d": 4, "e": 5}

    def test_merge_dictionaries_with_overlap(self):
        """Test merge_dictionaries with overlapping keys (later values win)"""
        dict1 = {"a": 1, "b": 2, "c": 3}
        dict2 = {"b": 20, "d": 4}
        dict3 = {"c": 30, "e": 5}

        result = merge_dictionaries(dict1, dict2, dict3)
        assert result == {"a": 1, "b": 20, "c": 30, "d": 4, "e": 5}

    def test_merge_dictionaries_empty_dicts(self):
        """Test merge_dictionaries with empty dictionaries"""
        dict1 = {}
        dict2 = {"a": 1}
        dict3 = {}

        result = merge_dictionaries(dict1, dict2, dict3)
        assert result == {"a": 1}

    def test_merge_dictionaries_preserves_originals(self):
        """Test that merge_dictionaries doesn't modify original dictionaries"""
        dict1 = {"a": 1, "b": 2}
        dict2 = {"b": 20, "c": 3}

        original_dict1 = dict1.copy()
        original_dict2 = dict2.copy()

        result = merge_dictionaries(dict1, dict2)

        # Verify originals are unchanged
        assert dict1 == original_dict1
        assert dict2 == original_dict2

        # Verify merge result
        assert result == {"a": 1, "b": 20, "c": 3}

    def test_merge_dictionaries_complex_values(self):
        """Test merge_dictionaries with complex values"""
        dict1 = {"list": [1, 2], "dict": {"nested": "value1"}}
        dict2 = {"list": [3, 4], "string": "test"}

        result = merge_dictionaries(dict1, dict2)
        assert result == {
            "list": [3, 4],  # Later value wins
            "dict": {"nested": "value1"},
            "string": "test"
        }
