"""Deprecation decorator for backward compatibility."""
import functools
import warnings
from typing import Callable, TypeVar

F = TypeVar('F', bound=Callable)


def deprecated(message: str):
    """Mark a function or class as deprecated.

    Args:
        message: Deprecation message to display

    Returns:
        Decorated function or class that shows deprecation warning
    """
    def decorator(obj):
        if isinstance(obj, type):
            # For classes
            original_init = obj.__init__

            def new_init(self, *args, **kwargs):
                warnings.warn(
                    f"{obj.__name__} is deprecated. {message}",
                    category=DeprecationWarning,
                    stacklevel=2
                )
                return original_init(self, *args, **kwargs)

            obj.__init__ = new_init
            return obj
        # For functions/methods
        @functools.wraps(obj)
        def wrapper(*args, **kwargs):
            warnings.warn(
                f"{obj.__name__} is deprecated. {message}",
                category=DeprecationWarning,
                stacklevel=2
            )
            return obj(*args, **kwargs)
        return wrapper
    return decorator
