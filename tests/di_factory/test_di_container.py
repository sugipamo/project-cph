from unittest.mock import Mock, patch

import pytest

from src.infrastructure.config.di_config import (
    _create_contest_manager,
    _create_system_config_loader,
    configure_production_dependencies,
    configure_test_dependencies,
)
from src.infrastructure.di_container import DIContainer


def test_register_and_resolve():
    container = DIContainer()
    container.register("int_provider", lambda: 42)
    container.register("str_provider", lambda: "hello")
    assert container.resolve("int_provider") == 42
    assert container.resolve("str_provider") == "hello"
    # 複数回resolveしても新しいインスタンスが返る（関数が呼ばれる）
    assert container.resolve("int_provider") == 42

def test_resolve_unregistered_key():
    container = DIContainer()
    with pytest.raises(ValueError) as e:
        container.resolve("not_registered")
    assert "not_registered" in str(e.value)


class TestDIConfigFactories:
    """Test DI configuration factory functions"""

    def test_create_system_config_loader(self):
        """Test _create_system_config_loader factory"""
        container = Mock()

        loader = _create_system_config_loader(container)

        assert loader is not None
        # Should be SystemConfigLoader instance
        assert hasattr(loader, 'get_env_config')

    # @patch('src.workflow.problem_workspace_service.ProblemWorkspaceService')
    # def test_create_problem_workspace_service(self, mock_service_class):
    #     """Test _create_problem_workspace_service factory"""
    #     container = Mock()
    #
    #     # Mock dependencies
    #     mock_file_driver = Mock()
    #     mock_repository = Mock()
    #     mock_logger = Mock()
    #     mock_config_loader = Mock()
    #     mock_config_loader.get_env_config.return_value = {
    #         "languages": {
    #             "python": {"paths": {"contest_current_path": "/current"}}
    #         },
    #         "shared": {"paths": {"workspace_path": "/workspace"}}
    #     }
    #
    #     def mock_resolve(key):
    #         if key == "file_driver":
    #             return mock_file_driver
    #         if key == "logger":
    #             return mock_logger
    #         if key == "system_config_loader":
    #             return mock_config_loader
    #         return Mock()
    #
    #     container.resolve.side_effect = mock_resolve
    #
    #     mock_service_instance = Mock()
    #     mock_service_class.return_value = mock_service_instance
    #
    #     result = _create_problem_workspace_service(container)
    #
    #     assert result == mock_service_instance
    #     mock_service_class.assert_called_once()

    # @patch('src.infrastructure.drivers.workspace.workspace_driver.WorkspaceDriver')
    # def test_create_workspace_driver(self, mock_driver_class):
    #     """Test _create_workspace_driver factory"""
    #     container = Mock()
    #     mock_workspace_service = Mock()
    #     container.resolve.return_value = mock_workspace_service
    #
    #     mock_driver_instance = Mock()
    #     mock_driver_class.return_value = mock_driver_instance
    #
    #     result = _create_workspace_driver(container)
    #
    #     assert result == mock_driver_instance
    #     mock_driver_class.assert_called_once_with(mock_workspace_service)

    @patch('src.infrastructure.persistence.sqlite.contest_manager.ContestManager')
    def test_create_contest_manager(self, mock_contest_manager_class):
        """Test _create_contest_manager factory"""
        container = Mock()

        mock_manager_instance = Mock()
        mock_contest_manager_class.return_value = mock_manager_instance

        result = _create_contest_manager(container)

        assert result == mock_manager_instance
        mock_contest_manager_class.assert_called_once_with(container, {})

    def test_configure_production_dependencies_includes_new_factories(self):
        """Test that configure_production_dependencies includes new factories"""
        container = DIContainer()

        configure_production_dependencies(container)

        # Test that new dependencies are registered
        assert "system_config_loader" in container._providers
        assert "contest_manager" in container._providers

    def test_configure_test_dependencies_includes_new_factories(self):
        """Test that configure_test_dependencies includes new factories"""
        container = DIContainer()

        configure_test_dependencies(container)

        # Test that new dependencies are registered
        assert "system_config_loader" in container._providers
        assert "contest_manager" in container._providers

    @patch('src.infrastructure.config.di_config._create_system_config_loader')
    def test_factory_dependency_resolution(self, mock_create_config_loader):
        """Test that factories correctly resolve dependencies"""
        container = DIContainer()
        configure_production_dependencies(container)

        mock_config_loader = Mock()
        mock_create_config_loader.return_value = mock_config_loader

        # Resolve system_config_loader
        loader = container.resolve("system_config_loader")
        assert loader == mock_config_loader

    def test_lazy_loading_behavior(self):
        """Test that factories use lazy loading correctly"""
        container = DIContainer()
        configure_production_dependencies(container)

        # Initially, dependencies should not be instantiated
        # Only after resolve() should they be created

        # This test verifies the lazy loading pattern is working
        # by checking that factories are callable objects
        assert callable(container._providers["system_config_loader"])
        assert callable(container._providers["contest_manager"])
