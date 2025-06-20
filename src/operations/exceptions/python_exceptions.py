"""Python-specific exception classes for structured error handling."""


class PythonConfigError(Exception):
    """Raised when there's an issue with Python configuration."""
    pass


class PythonEnvironmentError(Exception):
    """Raised when there's an issue with Python environment detection."""
    pass


class PythonVersionError(Exception):
    """Raised when there's an issue with Python version validation."""
    pass


class PythonInterpreterError(Exception):
    """Raised when Python interpreter cannot be found or accessed."""
    pass
