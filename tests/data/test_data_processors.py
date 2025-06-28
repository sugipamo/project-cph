"""Tests for data processors module"""
import pytest
from src.data.data_processors import (
    filter_and_transform_items,
    group_items_by_key,
    merge_dictionaries
)


class TestFilterAndTransformItems:
    """Tests for filter_and_transform_items function"""
    
    def test_filter_and_transform_with_numbers(self):
        """Test filtering even numbers and doubling them"""
        items = [1, 2, 3, 4, 5, 6]
        filter_func = lambda x: x % 2 == 0
        transform_func = lambda x: x * 2
        
        result = filter_and_transform_items(items, filter_func, transform_func)
        
        assert result == [4, 8, 12]
    
    def test_filter_and_transform_with_strings(self):
        """Test filtering strings by length and converting to uppercase"""
        items = ["hello", "hi", "world", "a", "test"]
        filter_func = lambda x: len(x) > 2
        transform_func = lambda x: x.upper()
        
        result = filter_and_transform_items(items, filter_func, transform_func)
        
        assert result == ["HELLO", "WORLD", "TEST"]
    
    def test_filter_and_transform_empty_list(self):
        """Test with empty list"""
        items = []
        filter_func = lambda x: True
        transform_func = lambda x: x
        
        result = filter_and_transform_items(items, filter_func, transform_func)
        
        assert result == []
    
    def test_filter_and_transform_no_matches(self):
        """Test when no items match filter"""
        items = [1, 3, 5, 7]
        filter_func = lambda x: x % 2 == 0
        transform_func = lambda x: x * 2
        
        result = filter_and_transform_items(items, filter_func, transform_func)
        
        assert result == []
    
    def test_filter_and_transform_complex_objects(self):
        """Test with dictionaries"""
        items = [
            {"name": "Alice", "age": 30},
            {"name": "Bob", "age": 25},
            {"name": "Charlie", "age": 35}
        ]
        filter_func = lambda x: x["age"] > 25
        transform_func = lambda x: x["name"]
        
        result = filter_and_transform_items(items, filter_func, transform_func)
        
        assert result == ["Alice", "Charlie"]


class TestGroupItemsByKey:
    """Tests for group_items_by_key function"""
    
    def test_group_by_modulo(self):
        """Test grouping numbers by modulo"""
        items = [1, 2, 3, 4, 5, 6]
        key_func = lambda x: x % 2
        
        result = group_items_by_key(items, key_func)
        
        assert result == {
            0: [2, 4, 6],
            1: [1, 3, 5]
        }
    
    def test_group_by_string_length(self):
        """Test grouping strings by length"""
        items = ["a", "bb", "ccc", "dd", "e", "fff"]
        key_func = lambda x: len(x)
        
        result = group_items_by_key(items, key_func)
        
        assert result == {
            1: ["a", "e"],
            2: ["bb", "dd"],
            3: ["ccc", "fff"]
        }
    
    def test_group_empty_list(self):
        """Test grouping empty list"""
        items = []
        key_func = lambda x: x
        
        result = group_items_by_key(items, key_func)
        
        assert result == {}
    
    def test_group_single_group(self):
        """Test when all items belong to same group"""
        items = [2, 4, 6, 8]
        key_func = lambda x: "even"
        
        result = group_items_by_key(items, key_func)
        
        assert result == {"even": [2, 4, 6, 8]}
    
    def test_group_complex_objects(self):
        """Test grouping dictionaries by field"""
        items = [
            {"type": "fruit", "name": "apple"},
            {"type": "vegetable", "name": "carrot"},
            {"type": "fruit", "name": "banana"},
            {"type": "vegetable", "name": "potato"}
        ]
        key_func = lambda x: x["type"]
        
        result = group_items_by_key(items, key_func)
        
        assert result == {
            "fruit": [
                {"type": "fruit", "name": "apple"},
                {"type": "fruit", "name": "banana"}
            ],
            "vegetable": [
                {"type": "vegetable", "name": "carrot"},
                {"type": "vegetable", "name": "potato"}
            ]
        }
    
    def test_group_preserves_order(self):
        """Test that grouping preserves original order within groups"""
        items = ["a1", "b1", "a2", "b2", "a3"]
        key_func = lambda x: x[0]
        
        result = group_items_by_key(items, key_func)
        
        assert result == {
            "a": ["a1", "a2", "a3"],
            "b": ["b1", "b2"]
        }


class TestMergeDictionaries:
    """Tests for merge_dictionaries function"""
    
    def test_merge_two_dictionaries(self):
        """Test merging two dictionaries"""
        dict1 = {"a": 1, "b": 2}
        dict2 = {"c": 3, "d": 4}
        
        result = merge_dictionaries(dict1, dict2)
        
        assert result == {"a": 1, "b": 2, "c": 3, "d": 4}
    
    def test_merge_overlapping_keys(self):
        """Test that later dictionaries override earlier ones"""
        dict1 = {"a": 1, "b": 2}
        dict2 = {"b": 3, "c": 4}
        dict3 = {"c": 5, "d": 6}
        
        result = merge_dictionaries(dict1, dict2, dict3)
        
        assert result == {"a": 1, "b": 3, "c": 5, "d": 6}
    
    def test_merge_empty_dictionaries(self):
        """Test merging empty dictionaries"""
        result = merge_dictionaries({}, {}, {})
        
        assert result == {}
    
    def test_merge_single_dictionary(self):
        """Test merging single dictionary"""
        dict1 = {"a": 1, "b": 2}
        
        result = merge_dictionaries(dict1)
        
        assert result == {"a": 1, "b": 2}
    
    def test_merge_no_dictionaries(self):
        """Test merging no dictionaries"""
        result = merge_dictionaries()
        
        assert result == {}
    
    def test_merge_nested_dictionaries(self):
        """Test merging dictionaries with nested values"""
        dict1 = {"a": {"x": 1}, "b": 2}
        dict2 = {"a": {"y": 2}, "c": 3}
        
        result = merge_dictionaries(dict1, dict2)
        
        # Note: nested dictionaries are replaced, not merged
        assert result == {"a": {"y": 2}, "b": 2, "c": 3}
    
    def test_merge_preserves_types(self):
        """Test that merge preserves value types"""
        dict1 = {"str": "hello", "int": 42, "list": [1, 2, 3]}
        dict2 = {"float": 3.14, "bool": True, "none": None}
        
        result = merge_dictionaries(dict1, dict2)
        
        assert result == {
            "str": "hello",
            "int": 42,
            "list": [1, 2, 3],
            "float": 3.14,
            "bool": True,
            "none": None
        }