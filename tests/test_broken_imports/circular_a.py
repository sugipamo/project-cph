"""Module A for circular import testing"""

# This will create a circular import with circular_b.py
from test_broken_imports.circular_b import function_b

def function_a():
    """Function in module A"""
    print("Function A")
    return function_b()

def helper_a():
    """Helper function"""
    return "Helper A"