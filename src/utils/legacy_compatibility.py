"""Backward compatibility module for utility functions

DEPRECATED: This module will be removed in a future version.
Use the specific modules instead:
- src.utils.string_formatters for string and template operations
- src.utils.docker_wrappers for Docker command wrappers
- src.utils.data_processors for data processing functions
"""
import warnings

# Re-export functions with deprecation warnings for backward compatibility

# Issue deprecation warning when this module is imported
warnings.warn(
    "src.utils.helpers is deprecated. Use specific modules instead: "
    "string_formatters, docker_wrappers, or data_processors",
    DeprecationWarning,
    stacklevel=2
)


