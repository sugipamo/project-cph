"""Dependency injection module - 副作用プロバイダーの依存性注入"""

from .provider_factory import (
    ProviderFactory,
    get_console_logger,
    get_environment_provider,
    get_file_provider,
    get_provider_factory,
    get_time_provider,
    initialize_providers,
)

__all__ = [
    'ProviderFactory',
    'get_console_logger',
    'get_environment_provider',
    'get_file_provider',
    'get_provider_factory',
    'get_time_provider',
    'initialize_providers'
]
