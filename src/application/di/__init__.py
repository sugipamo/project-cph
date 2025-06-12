"""Dependency injection module - 副作用プロバイダーの依存性注入"""

from .provider_factory import (
    ProviderFactory, 
    initialize_providers, 
    get_provider_factory,
    get_file_provider,
    get_time_provider, 
    get_environment_provider,
    get_console_logger
)

__all__ = [
    'ProviderFactory',
    'initialize_providers',
    'get_provider_factory', 
    'get_file_provider',
    'get_time_provider',
    'get_environment_provider',
    'get_console_logger'
]