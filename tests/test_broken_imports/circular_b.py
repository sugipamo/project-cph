"""Module B for circular import testing"""

# This will create a circular import with circular_a.py
from test_broken_imports.circular_a import function_a

def function_b():
    """Function in module B"""
    print("Function B")
    return "Result from B"

def call_a():
    """Function that calls A"""
    return function_a()