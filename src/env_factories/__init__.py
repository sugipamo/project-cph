"""
Request factory module

Unified factory pattern for generating operation requests.
Replaces multiple specialized factories with a single, configurable factory.
"""

from .unified_factory import UnifiedCommandRequestFactory
from .unified_selector import UnifiedFactorySelector, get_unified_factory, get_factory_for_step_type
from .command_types import CommandType
from .base.factory import BaseCommandRequestFactory

# Backward compatibility (avoid circular import)
try:
    from .selector import RequestFactorySelector
except ImportError:
    RequestFactorySelector = None

__all__ = [
    # New unified pattern (recommended)
    "UnifiedCommandRequestFactory",
    "UnifiedFactorySelector", 
    "CommandType",
    "get_unified_factory",
    "get_factory_for_step_type",
    
    # Base classes
    "BaseCommandRequestFactory",
    
    # Legacy (deprecated)
    "RequestFactorySelector"
]