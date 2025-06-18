"""Tests for provider factory."""
from pathlib import Path
from unittest.mock import patch

import pytest

from src.application.di.provider_factory import (
    ProviderFactory,
    get_console_logger,
    get_environment_provider,
    get_file_provider,
    get_provider_factory,
    get_time_provider,
    initialize_providers,
)
from src.configuration.config_manager import TypeSafeConfigNodeManager
from src.infrastructure.providers import (
    EnvironmentProvider,
    FileProvider,
    RegistryProvider,
    TimeProvider,
    WorkingDirectoryProvider,
)


class TestProviderFactory:
    """Test ProviderFactory implementation."""

    def test_init_system_providers(self):
        factory = ProviderFactory(use_mocks=False)
        assert not factory.use_mocks
        assert len(factory._providers) > 0

    def test_init_mock_providers(self):
        factory = ProviderFactory(use_mocks=True)
        assert factory.use_mocks
        assert len(factory._providers) > 0

    def test_get_file_provider_system(self):
        factory = ProviderFactory(use_mocks=False)
        provider = factory.get_file_provider()
        assert isinstance(provider, FileProvider)

    def test_get_file_provider_mock(self):
        factory = ProviderFactory(use_mocks=True)
        provider = factory.get_file_provider()
        assert isinstance(provider, FileProvider)

    def test_get_time_provider_system(self):
        factory = ProviderFactory(use_mocks=False)
        provider = factory.get_time_provider()
        assert isinstance(provider, TimeProvider)

    def test_get_time_provider_mock(self):
        factory = ProviderFactory(use_mocks=True)
        provider = factory.get_time_provider()
        assert isinstance(provider, TimeProvider)

    def test_get_environment_provider_system(self):
        factory = ProviderFactory(use_mocks=False)
        provider = factory.get_environment_provider()
        assert isinstance(provider, EnvironmentProvider)

    def test_get_environment_provider_mock(self):
        factory = ProviderFactory(use_mocks=True)
        provider = factory.get_environment_provider()
        assert isinstance(provider, EnvironmentProvider)

    def test_get_working_directory_provider_system(self):
        factory = ProviderFactory(use_mocks=False)
        provider = factory.get_working_directory_provider()
        assert isinstance(provider, WorkingDirectoryProvider)

    def test_get_working_directory_provider_mock(self):
        factory = ProviderFactory(use_mocks=True)
        provider = factory.get_working_directory_provider()
        assert isinstance(provider, WorkingDirectoryProvider)

    def test_get_registry_provider_system(self):
        factory = ProviderFactory(use_mocks=False)
        provider = factory.get_registry_provider()
        assert isinstance(provider, RegistryProvider)

    def test_get_registry_provider_mock(self):
        factory = ProviderFactory(use_mocks=True)
        provider = factory.get_registry_provider()
        assert isinstance(provider, RegistryProvider)



    def test_get_config_manager_system(self):
        factory = ProviderFactory(use_mocks=False)
        manager = factory.get_config_manager()
        assert isinstance(manager, TypeSafeConfigNodeManager)

    def test_get_config_manager_mock(self):
        factory = ProviderFactory(use_mocks=True)
        manager = factory.get_config_manager()
        assert isinstance(manager, TypeSafeConfigNodeManager)

    def test_reset_providers(self):
        factory = ProviderFactory(use_mocks=False)
        original_providers = dict(factory._providers)

        factory._providers.clear()
        assert len(factory._providers) == 0

        factory.reset_providers()
        assert len(factory._providers) == len(original_providers)

    def test_initialize_providers_function(self):
        factory = initialize_providers(use_mocks=False)
        assert isinstance(factory, ProviderFactory)
        assert not factory.use_mocks

        factory = initialize_providers(use_mocks=True)
        assert isinstance(factory, ProviderFactory)
        assert factory.use_mocks

    def test_get_provider_factory_function(self):
        factory = get_provider_factory(use_mocks=False)
        assert isinstance(factory, ProviderFactory)
        assert not factory.use_mocks

        factory = get_provider_factory(use_mocks=True)
        assert isinstance(factory, ProviderFactory)
        assert factory.use_mocks

    def test_convenience_functions(self):
        file_provider = get_file_provider()
        assert isinstance(file_provider, FileProvider)

        time_provider = get_time_provider()
        assert isinstance(time_provider, TimeProvider)

        env_provider = get_environment_provider()
        assert isinstance(env_provider, EnvironmentProvider)

    def test_provider_singleton_behavior(self):
        factory = ProviderFactory(use_mocks=False)

        provider1 = factory.get_file_provider()
        provider2 = factory.get_file_provider()

        assert provider1 is provider2

    def test_system_providers_initialization_paths(self):
        factory = ProviderFactory(use_mocks=False)
        manager = factory.get_config_manager()

        # TypeSafeConfigNodeManagerが正しく初期化されているかテスト
        assert isinstance(manager, TypeSafeConfigNodeManager)

    def test_mock_providers_initialization_paths(self):
        factory = ProviderFactory(use_mocks=True)
        manager = factory.get_config_manager()

        # TypeSafeConfigNodeManagerが正しく初期化されているかテスト
        assert isinstance(manager, TypeSafeConfigNodeManager)


