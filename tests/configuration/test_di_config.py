"""Tests for DI configuration."""
import pytest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

from src.configuration.di_config import (
    configure_production_dependencies,
    configure_test_dependencies,
    _create_shell_driver,
    _create_docker_driver,
    _create_file_driver,
    _create_python_driver,
    _create_persistence_driver,
    _create_shell_python_driver,
    _create_sqlite_manager,
    _create_operation_repository,
    _create_session_repository,
    _create_docker_container_repository,
    _create_docker_image_repository,
    _create_system_config_repository,
    _create_unified_driver,
    _create_execution_controller,
    _create_output_manager,
    _create_environment_manager,
    _create_logger,
    _create_logging_output_manager,
    _create_mock_logging_output_manager,
    _create_application_logger_adapter,
    _create_workflow_logger_adapter,
    _create_unified_logger,
    _create_filesystem,
    _create_request_factory,
    _create_system_config_loader,
    _create_file_pattern_service,
    _create_json_config_loader,
    _create_contest_manager,
    _create_json_provider,
    _create_sqlite_provider,
    _create_mock_json_provider,
    _create_mock_sqlite_provider,
    _create_configuration_repository,
    _create_os_provider,
    _create_mock_os_provider,
    _create_sys_provider,
    _create_mock_sys_provider,
)
from src.infrastructure.di_container import DIContainer, DIKey


class TestFactoryFunctions:
    """Test individual factory functions."""

    def test_create_shell_driver(self):
        """Test shell driver factory returns None (backward compatibility)."""
        result = _create_shell_driver(Mock())
        assert result is None

    def test_create_docker_driver(self):
        """Test docker driver factory."""
        container = Mock()
        container.resolve.side_effect = lambda key: Mock()
        
        driver = _create_docker_driver(container)
        
        # Verify it resolved all dependencies
        expected_keys = [
            DIKey.FILE_DRIVER,
            DIKey.SHELL_PYTHON_DRIVER,
            DIKey.LOGGER,
            DIKey.DOCKER_CONTAINER_REPOSITORY,
            DIKey.DOCKER_IMAGE_REPOSITORY
        ]
        for key in expected_keys:
            container.resolve.assert_any_call(key)

    def test_create_file_driver(self):
        """Test file driver factory."""
        container = Mock()
        container.resolve.return_value = Mock()  # Mock logger
        
        driver = _create_file_driver(container)
        
        container.resolve.assert_called_once_with(DIKey.LOGGER)

    def test_create_python_driver(self):
        """Test python driver factory returns ExecutionDriver."""
        container = Mock()
        mock_driver = Mock()
        container.resolve.return_value = mock_driver
        
        driver = _create_python_driver(container)
        
        assert driver == mock_driver
        container.resolve.assert_called_once_with(DIKey.SHELL_PYTHON_DRIVER)

    def test_create_persistence_driver(self):
        """Test persistence driver factory."""
        driver = _create_persistence_driver()
        assert driver is not None

    def test_create_shell_python_driver(self):
        """Test shell/python driver factory."""
        container = Mock()
        container.resolve.side_effect = lambda key: Mock()
        
        driver = _create_shell_python_driver(container)
        
        # Verify it resolved config_manager and file_driver
        container.resolve.assert_any_call(DIKey.CONFIG_MANAGER)
        container.resolve.assert_any_call(DIKey.FILE_DRIVER)

    def test_create_sqlite_manager(self):
        """Test SQLite manager factory."""
        container = Mock()
        mock_provider = Mock()
        container.resolve.return_value = mock_provider
        
        manager = _create_sqlite_manager(container)
        
        container.resolve.assert_called_once_with(DIKey.SQLITE_PROVIDER)

    def test_create_operation_repository(self):
        """Test operation repository factory."""
        container = Mock()
        container.resolve.side_effect = lambda key: Mock()
        
        repo = _create_operation_repository(container)
        
        container.resolve.assert_any_call(DIKey.SQLITE_MANAGER)
        container.resolve.assert_any_call(DIKey.JSON_PROVIDER)

    def test_create_session_repository(self):
        """Test session repository factory."""
        sqlite_manager = Mock()
        repo = _create_session_repository(sqlite_manager)
        assert repo is not None

    def test_create_docker_container_repository(self):
        """Test docker container repository factory."""
        sqlite_manager = Mock()
        repo = _create_docker_container_repository(sqlite_manager)
        assert repo is not None

    def test_create_docker_image_repository(self):
        """Test docker image repository factory."""
        sqlite_manager = Mock()
        repo = _create_docker_image_repository(sqlite_manager)
        assert repo is not None

    def test_create_system_config_repository(self):
        """Test system config repository factory."""
        container = Mock()
        container.resolve.side_effect = lambda key: Mock()
        
        repo = _create_system_config_repository(container)
        
        container.resolve.assert_any_call(DIKey.SQLITE_MANAGER)
        container.resolve.assert_any_call("json_config_loader")

    def test_create_unified_driver(self):
        """Test unified driver factory."""
        container = Mock()
        container.resolve.side_effect = lambda key: Mock()
        
        driver = _create_unified_driver(container)
        
        container.resolve.assert_any_call(DIKey.UNIFIED_LOGGER)
        container.resolve.assert_any_call(DIKey.CONFIG_MANAGER)

    def test_create_execution_controller(self):
        """Test execution controller factory returns None (removed)."""
        result = _create_execution_controller()
        assert result is None

    def test_create_output_manager(self):
        """Test output manager factory returns None (removed)."""
        result = _create_output_manager()
        assert result is None

    def test_create_environment_manager(self):
        """Test environment manager factory."""
        container = Mock()
        container.resolve.side_effect = lambda key: Mock()
        
        manager = _create_environment_manager(container)
        
        container.resolve.assert_any_call(DIKey.CONFIG_MANAGER)
        container.resolve.assert_any_call(DIKey.LOGGER)

    def test_create_logger(self):
        """Test logger factory uses unified logger."""
        container = Mock()
        mock_logger = Mock()
        
        with patch('src.configuration.di_config._create_unified_logger', return_value=mock_logger):
            logger = _create_logger(container)
            assert logger == mock_logger

    def test_create_logging_output_manager(self):
        """Test logging output manager factory."""
        manager = _create_logging_output_manager()
        assert manager.name == "output"

    def test_create_mock_logging_output_manager(self):
        """Test mock logging output manager factory."""
        manager = _create_mock_logging_output_manager()
        assert manager.name == "mock_output"

    def test_create_application_logger_adapter(self):
        """Test application logger adapter factory."""
        container = Mock()
        mock_output_manager = Mock()
        container.resolve.return_value = mock_output_manager
        
        adapter = _create_application_logger_adapter(container)
        
        container.resolve.assert_called_once_with(DIKey.LOGGING_OUTPUT_MANAGER)

    def test_create_workflow_logger_adapter(self):
        """Test workflow logger adapter factory."""
        container = Mock()
        mock_output_manager = Mock()
        container.resolve.return_value = mock_output_manager
        
        adapter = _create_workflow_logger_adapter(container)
        
        container.resolve.assert_called_once_with(DIKey.LOGGING_OUTPUT_MANAGER)

    def test_create_unified_logger(self):
        """Test unified logger factory."""
        container = Mock()
        mock_output_manager = Mock()
        container.resolve.return_value = mock_output_manager
        
        logger = _create_unified_logger(container)
        
        container.resolve.assert_called_once_with(DIKey.LOGGING_OUTPUT_MANAGER)

    def test_create_filesystem(self):
        """Test filesystem factory."""
        fs = _create_filesystem()
        assert fs is not None

    def test_create_request_factory(self):
        """Test request factory."""
        container = Mock()
        mock_config_manager = Mock()
        container.resolve.return_value = mock_config_manager
        
        factory = _create_request_factory(container)
        
        container.resolve.assert_called_once_with(DIKey.CONFIG_MANAGER)

    def test_create_system_config_loader(self):
        """Test system config loader factory."""
        container = Mock()
        loader = _create_system_config_loader(container)
        assert loader is not None

    def test_create_file_pattern_service(self):
        """Test file pattern service factory returns None (disabled)."""
        result = _create_file_pattern_service(Mock())
        assert result is None

    def test_create_json_config_loader(self):
        """Test JSON config loader factory."""
        container = Mock()
        
        # Test when CONFIG_MANAGER is not registered
        container.is_registered.return_value = False
        result = _create_json_config_loader(container)
        assert result is None
        
        # Test when CONFIG_MANAGER is registered
        container.is_registered.return_value = True
        mock_config = Mock()
        container.resolve.return_value = mock_config
        result = _create_json_config_loader(container)
        assert result == mock_config

    def test_create_contest_manager(self):
        """Test contest manager factory."""
        container = Mock()
        manager = _create_contest_manager(container)
        assert manager is not None

    def test_create_json_provider(self):
        """Test JSON provider factory."""
        provider = _create_json_provider()
        assert provider is not None

    def test_create_sqlite_provider(self):
        """Test SQLite provider factory."""
        provider = _create_sqlite_provider()
        assert provider is not None

    def test_create_mock_json_provider(self):
        """Test mock JSON provider factory."""
        provider = _create_mock_json_provider()
        assert provider is not None

    def test_create_mock_sqlite_provider(self):
        """Test mock SQLite provider factory."""
        provider = _create_mock_sqlite_provider()
        assert provider is not None

    def test_create_configuration_repository(self):
        """Test configuration repository factory."""
        container = Mock()
        container.resolve.side_effect = lambda key: Mock()
        
        repo = _create_configuration_repository(container)
        
        container.resolve.assert_any_call(DIKey.JSON_PROVIDER)
        container.resolve.assert_any_call(DIKey.SQLITE_PROVIDER)

    def test_create_os_provider(self):
        """Test OS provider factory."""
        provider = _create_os_provider()
        assert provider is not None

    def test_create_mock_os_provider(self):
        """Test mock OS provider factory."""
        provider = _create_mock_os_provider()
        assert provider is not None

    def test_create_sys_provider(self):
        """Test sys provider factory."""
        container = Mock()
        provider = _create_sys_provider(container)
        assert provider is not None

    def test_create_mock_sys_provider(self):
        """Test mock sys provider factory."""
        provider = _create_mock_sys_provider()
        assert provider is not None
        assert provider.argv == ["test_program"]
        assert provider.platform == "test"


class TestDependencyConfiguration:
    """Test dependency configuration functions."""

    def test_configure_production_dependencies(self):
        """Test production dependency configuration."""
        container = DIContainer()
        configure_production_dependencies(container)
        
        # Verify key dependencies are registered
        assert container.is_registered(DIKey.JSON_PROVIDER)
        assert container.is_registered(DIKey.SQLITE_PROVIDER)
        assert container.is_registered(DIKey.FILE_DRIVER)
        assert container.is_registered(DIKey.DOCKER_DRIVER)
        assert container.is_registered(DIKey.UNIFIED_LOGGER)
        assert container.is_registered(DIKey.CONFIG_MANAGER)
        
        # Verify string aliases
        assert container.is_registered('file_driver')
        assert container.is_registered('docker_driver')
        assert container.is_registered('unified_logger')

    def test_configure_test_dependencies(self):
        """Test test dependency configuration."""
        container = DIContainer()
        configure_test_dependencies(container)
        
        # Verify mock dependencies are registered
        assert container.is_registered(DIKey.JSON_PROVIDER)
        assert container.is_registered(DIKey.SQLITE_PROVIDER)
        assert container.is_registered(DIKey.FILE_DRIVER)
        assert container.is_registered(DIKey.DOCKER_DRIVER)
        assert container.is_registered(DIKey.UNIFIED_LOGGER)
        
        # Verify string aliases
        assert container.is_registered('file_driver')
        assert container.is_registered('docker_driver')
        assert container.is_registered('unified_logger')