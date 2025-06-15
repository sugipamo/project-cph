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
    def decorator(deprecated_item):
        if isinstance(deprecated_item, type):
            # For classes
            original_init = deprecated_item.__init__

            def new_init(self, *args, **kwargs):
                warnings.warn(
                    f"{deprecated_item.__name__} is deprecated. {message}",
                    category=DeprecationWarning,
                    stacklevel=2
                )
                return original_init(self, *args, **kwargs)

            deprecated_item.__init__ = new_init
            return deprecated_item
        # For functions/methods
        @functools.wraps(deprecated_item)
        def wrapper(*args, **kwargs):
            warnings.warn(
                f"{deprecated_item.__name__} is deprecated. {message}",
                category=DeprecationWarning,
                stacklevel=2
            )
            return deprecated_item(*args, **kwargs)
        return wrapper
    return decorator
