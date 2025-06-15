"""Data processing and manipulation utilities

Pure functions for list processing, dictionary operations, and data transformations.
All functions are stateless with no side effects, following functional programming principles.
"""
from typing import Any


def filter_and_transform_items(items: list[Any], filter_func, transform_func) -> list[Any]:
    """Pure function to filter and transform list items

    Args:
        items: List of items to process
        filter_func: Function to filter items
        transform_func: Function to transform items

    Returns:
        Filtered and transformed list
    """
    return [transform_func(item) for item in items if filter_func(item)]


def group_items_by_key(items: list[Any], key_func) -> dict[Any, list[Any]]:
    """Pure function to group list items by key

    Args:
        items: List of items to group
        key_func: Function to extract grouping key

    Returns:
        Dictionary with grouped items
    """
    groups = {}
    for item in items:
        key = key_func(item)
        if key not in groups:
            groups[key] = []
        groups[key].append(item)
    return groups


def merge_dictionaries(*dicts: dict[str, Any]) -> dict[str, Any]:
    """Pure function to merge multiple dictionaries

    Args:
        *dicts: Dictionaries to merge

    Returns:
        Merged dictionary
    """
    merged_dict = {}
    for d in dicts:
        merged_dict.update(d)
    return merged_dict
