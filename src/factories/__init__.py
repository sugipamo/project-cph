"""
Unified factories package - all factory patterns and builders
"""

# Driver factories
try:
    from ..operations.factory import DriverFactory
    driver_exports = ['DriverFactory']
except ImportError:
    driver_exports = []

# Environment factories
try:
    from ..env_factories import UnifiedFactory, UnifiedSelector, RequestBuilders
    env_exports = ['UnifiedFactory', 'UnifiedSelector', 'RequestBuilders']
except ImportError:
    env_exports = []

# Base factory patterns
try:
    from ..env_factories.base import Factory
    base_exports = ['Factory']
except ImportError:
    base_exports = []

# New unified factory system
try:
    from ..factory.abstract_factory import AbstractFactory
    from ..factory.factory_coordinator import FactoryCoordinator
    unified_exports = ['AbstractFactory', 'FactoryCoordinator']
except ImportError:
    unified_exports = []

__all__ = driver_exports + env_exports + base_exports + unified_exports