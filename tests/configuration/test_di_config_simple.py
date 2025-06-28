"""Simple tests for dependency injection configuration."""
import pytest
from unittest.mock import Mock, patch, MagicMock

from src.infrastructure.di_container import DIContainer, DIKey
from src.utils.types import LogLevel


class TestDIConfigBasics:
    """Test basic DI configuration functionality."""

    def test_di_container_basic_functionality(self):
        """Test that DIContainer works correctly."""
        container = DIContainer()
        
        # Test registration
        test_value = "test_value"
        container.register("test_key", lambda: test_value)
        assert container.is_registered("test_key")
        
        # Test resolution
        resolved = container.resolve("test_key")
        assert resolved == test_value

    def test_di_container_with_factory(self):
        """Test DIContainer with factory functions."""
        container = DIContainer()
        
        # Test with factory that has dependencies
        container.register("dependency", lambda: "dep_value")
        container.register("service", lambda: f"service_with_{container.resolve('dependency')}")
        
        result = container.resolve("service")
        assert result == "service_with_dep_value"

    def test_di_container_singleton_behavior(self):
        """Test that factories are called each time (not singleton by default)."""
        container = DIContainer()
        
        call_count = 0
        def factory():
            nonlocal call_count
            call_count += 1
            return f"instance_{call_count}"
        
        container.register("service", factory)
        
        # Each resolve should create a new instance
        instance1 = container.resolve("service")
        instance2 = container.resolve("service")
        
        assert instance1 == "instance_1"
        assert instance2 == "instance_2"
        assert call_count == 2

    @patch('src.configuration.di_config.OutputManager')
    @patch('src.configuration.di_config.MockOutputManager')
    def test_output_manager_factories(self, mock_mock_output, mock_output):
        """Test output manager factory functions."""
        from src.configuration.di_config import (
            _create_logging_output_manager,
            _create_mock_logging_output_manager
        )
        
        # Test production output manager
        prod_manager = _create_logging_output_manager()
        mock_output.assert_called_once_with(name="output", level=LogLevel.DEBUG)
        
        # Test mock output manager
        mock_manager = _create_mock_logging_output_manager()
        mock_mock_output.assert_called_once_with(name="mock_output", level=LogLevel.DEBUG)

    def test_provider_factories(self):
        """Test provider factory functions."""
        from src.configuration.di_config import (
            _create_json_provider,
            _create_sqlite_provider,
            _create_mock_json_provider,
            _create_mock_sqlite_provider,
            _create_os_provider,
            _create_mock_os_provider,
            _create_mock_sys_provider
        )
        
        # Test production providers
        json_provider = _create_json_provider()
        assert json_provider is not None
        assert type(json_provider).__name__ == 'SystemJsonProvider'
        
        sqlite_provider = _create_sqlite_provider()
        assert sqlite_provider is not None
        assert type(sqlite_provider).__name__ == 'SystemSQLiteProvider'
        
        os_provider = _create_os_provider()
        assert os_provider is not None
        assert type(os_provider).__name__ == 'SystemOsProvider'
        
        # Test mock providers
        mock_json = _create_mock_json_provider()
        assert mock_json is not None
        assert type(mock_json).__name__ == 'MockJsonProvider'
        
        mock_sqlite = _create_mock_sqlite_provider()
        assert mock_sqlite is not None
        assert type(mock_sqlite).__name__ == 'MockSQLiteProvider'
        
        mock_os = _create_mock_os_provider()
        assert mock_os is not None
        assert type(mock_os).__name__ == 'MockOsProvider'
        
        mock_sys = _create_mock_sys_provider()
        assert mock_sys is not None
        assert mock_sys.get_argv() == ["test_program"]
        assert mock_sys.get_platform() == "test"

    def test_utility_factories(self):
        """Test utility factory functions."""
        from src.configuration.di_config import (
            _create_execution_controller,
            _create_output_manager,
            _create_file_pattern_service,
            _create_persistence_driver
        )
        
        # Test factories that return None
        assert _create_execution_controller() is None
        assert _create_output_manager() is None
        assert _create_file_pattern_service(Mock()) is None
        
        # Test persistence driver
        driver = _create_persistence_driver()
        assert driver is not None
        assert type(driver).__name__ == 'SQLitePersistenceDriver'

    def test_json_config_loader_factory(self):
        """Test JSON config loader factory."""
        from src.configuration.di_config import _create_json_config_loader
        
        # Test when not registered
        container = Mock()
        container.is_registered.return_value = False
        
        loader = _create_json_config_loader(container)
        assert loader is None
        
        # Test when registered
        container = Mock()
        container.is_registered.return_value = True
        mock_config = Mock()
        container.resolve.return_value = mock_config
        
        loader = _create_json_config_loader(container)
        assert loader == mock_config
        
        # Test with exception
        container = Mock()
        container.is_registered.side_effect = Exception("Test error")
        
        loader = _create_json_config_loader(container)
        assert loader is None

    def test_filesystem_factory(self):
        """Test filesystem factory."""
        from src.configuration.di_config import _create_filesystem
        
        container = Mock()
        mock_config_manager = Mock()
        container.resolve.return_value = mock_config_manager
        
        fs = _create_filesystem(container)
        assert fs is not None
        assert type(fs).__name__ == 'LocalFileSystem'

    def test_contest_manager_factory(self):
        """Test contest manager factory."""
        from src.configuration.di_config import _create_contest_manager
        
        container = Mock()
        manager = _create_contest_manager(container)
        
        assert manager is not None
        assert manager.container == container
        # env_json is loaded lazily from file, so we just check the initial state
        assert manager._env_json == {}

    @patch('src.configuration.di_config.DIContainer')
    def test_configure_dependencies_registration_count(self, mock_container_class):
        """Test that configure functions register expected number of dependencies."""
        from src.configuration.di_config import (
            configure_production_dependencies,
            configure_test_dependencies
        )
        
        # Test production configuration
        prod_container = Mock()
        mock_container_class.return_value = prod_container
        
        configure_production_dependencies(prod_container)
        
        # Count the number of register calls
        register_calls = prod_container.register.call_count
        assert register_calls > 30  # Should register many dependencies
        
        # Test test configuration
        test_container = Mock()
        mock_container_class.return_value = test_container
        
        configure_test_dependencies(test_container)
        
        # Count the number of register calls
        test_register_calls = test_container.register.call_count
        assert test_register_calls > 30  # Should register many dependencies