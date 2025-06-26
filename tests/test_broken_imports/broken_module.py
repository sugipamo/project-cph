"""Module with broken imports for testing"""

# Non-existent module
import non_existent_module

# Non-existent from import
from fake_package import something

# Relative import that doesn't exist
from ..non_existent import other_thing

# Valid import (to mix with broken ones)
import os

def test_function():
    """Test function"""
    print("This is a test")
    return os.path.exists(".")