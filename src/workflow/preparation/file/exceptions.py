"""Exceptions for file pattern service functionality."""


class ConfigValidationError(Exception):
    """Raised when configuration validation fails."""
    pass


class PatternResolutionError(Exception):
    """Raised when pattern resolution fails."""
    pass