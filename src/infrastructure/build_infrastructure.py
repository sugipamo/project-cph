"""
Infrastructure builder with improved dependency management.
Uses lazy loading to reduce coupling and startup time.
"""
from src.infrastructure.di_container import DIContainer
from src.infrastructure.config.di_config import configure_production_dependencies, configure_test_dependencies


def build_infrastructure() -> DIContainer:
    """
    Setup and return infrastructure (DIContainer) with essential dependencies.
    Uses lazy loading to minimize coupling and improve startup performance.
    
    Returns:
        Configured DIContainer with all infrastructure components
    """
    container = DIContainer()
    configure_production_dependencies(container)
    return container


def build_mock_infrastructure() -> DIContainer:
    """
    Setup and return mock infrastructure (DIContainer) for testing.
    Uses lazy loading and mock implementations where available.
    
    Returns:
        Configured DIContainer with mock implementations
    """
    container = DIContainer()
    configure_test_dependencies(container)
    return container


# Backward compatibility aliases
build_operations = build_infrastructure
build_mock_operations = build_mock_infrastructure