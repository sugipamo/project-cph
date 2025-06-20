"""Tests for EnvironmentManager"""

from unittest.mock import Mock, patch

import pytest

from src.configuration.config_manager import TypeSafeConfigNodeManager
from src.infrastructure.environment.environment_manager import EnvironmentManager
from src.operations.requests.base.base_request import OperationRequestFoundation
from src.operations.results.result import OperationResult


class TestEnvironmentManager:
    """Tests for EnvironmentManager class"""

    def test_init_with_env_type(self):
        """Test initialization with explicit env_type"""
        manager = EnvironmentManager(env_type="docker")
        assert manager._env_type == "docker"

    def test_init_with_config_manager(self):
        """Test initialization with explicit config manager"""
        config_manager = Mock(spec=TypeSafeConfigNodeManager)
        manager = EnvironmentManager(env_type="local", config_manager=config_manager)
        assert manager._config_manager == config_manager
        assert manager._env_type == "local"

    @patch('src.infrastructure.environment.environment_manager.TypeSafeConfigNodeManager')
    def test_init_loads_config_when_no_env_type(self, mock_config_class):
        """Test initialization loads config when env_type not provided"""
        mock_config = Mock()
        mock_config.resolve_config.return_value = "test_env"
        mock_config_class.return_value = mock_config

        manager = EnvironmentManager()

        mock_config.load_from_files.assert_called_once_with(system_dir="config/system")
        mock_config.resolve_config.assert_called_once_with(['env_default', 'env_type'], str)
        assert manager._env_type == "test_env"

    @patch('src.infrastructure.environment.environment_manager.TypeSafeConfigNodeManager')
    def test_init_raises_error_when_no_config_found(self, mock_config_class):
        """Test initialization raises error when no config found"""
        mock_config = Mock()
        mock_config.resolve_config.side_effect = KeyError("config not found")
        mock_config_class.return_value = mock_config

        with pytest.raises(ValueError, match="Environment type not provided and no default env_type found"):
            EnvironmentManager()

    def test_prepare_environment(self):
        """Test prepare_environment method"""
        manager = EnvironmentManager(env_type="test")
        context = Mock()

        result = manager.prepare_environment(context)

        assert isinstance(result, OperationResult)
        assert result.success is True
        assert "Environment test prepared" in result.error_message

    def test_cleanup_environment(self):
        """Test cleanup_environment method"""
        manager = EnvironmentManager(env_type="test")
        context = Mock()

        result = manager.cleanup_environment(context)

        assert isinstance(result, OperationResult)
        assert result.success is True
        assert "Environment test cleaned up" in result.error_message

    def test_execute_request(self):
        """Test execute_request method"""
        manager = EnvironmentManager(env_type="test")
        request = Mock(spec=OperationRequestFoundation)
        driver = Mock()
        expected_result = Mock(spec=OperationResult)
        request.execute_operation.return_value = expected_result

        result = manager.execute_request(request, driver)

        request.execute_operation.assert_called_once_with(driver)
        assert result == expected_result

    def test_should_force_local_with_force_env_type_local(self):
        """Test should_force_local returns True when force_env_type is local"""
        manager = EnvironmentManager(env_type="docker")
        step_config = {"force_env_type": "local"}

        assert manager.should_force_local(step_config) is True

    def test_should_force_local_with_force_env_type_docker(self):
        """Test should_force_local returns False when force_env_type is docker and env_type is not local"""
        manager = EnvironmentManager(env_type="docker")
        step_config = {"force_env_type": "docker"}

        assert manager.should_force_local(step_config) is False

    def test_should_force_local_with_force_local_true(self):
        """Test should_force_local returns True when force_local is True (backwards compatibility)"""
        manager = EnvironmentManager(env_type="docker")
        step_config = {"force_local": True}

        assert manager.should_force_local(step_config) is True

    def test_should_force_local_with_force_local_false(self):
        """Test should_force_local returns False when force_local is False"""
        manager = EnvironmentManager(env_type="docker")
        step_config = {"force_local": False}

        assert manager.should_force_local(step_config) is False

    def test_should_force_local_with_local_env_type(self):
        """Test should_force_local returns True when env_type is local"""
        manager = EnvironmentManager(env_type="local")
        step_config = {}

        assert manager.should_force_local(step_config) is True

    def test_should_force_local_with_non_local_env_type(self):
        """Test should_force_local returns False when env_type is not local"""
        manager = EnvironmentManager(env_type="docker")
        step_config = {}

        assert manager.should_force_local(step_config) is False

    def test_get_working_directory(self):
        """Test get_working_directory method"""
        manager = EnvironmentManager(env_type="test")
        assert manager.get_working_directory() == "."

    def test_get_timeout(self):
        """Test get_timeout method"""
        manager = EnvironmentManager(env_type="test")
        assert manager.get_timeout() == 300

    def test_get_shell(self):
        """Test get_shell method"""
        manager = EnvironmentManager(env_type="test")
        assert manager.get_shell() == "bash"

    def test_get_workspace_root(self):
        """Test get_workspace_root method"""
        manager = EnvironmentManager(env_type="test")
        assert manager.get_workspace_root() == "./workspace"

    def test_from_context_with_env_type(self):
        """Test from_context class method with env_type"""
        context = Mock()
        context.env_type = "test_env"

        manager = EnvironmentManager.from_context(context)

        assert manager._env_type == "test_env"

    @patch('src.infrastructure.environment.environment_manager.TypeSafeConfigNodeManager')
    def test_from_context_without_env_type(self, mock_config_class):
        """Test from_context class method without env_type"""
        context = object()  # Plain object with no env_type attribute

        # Mock config to prevent loading issues
        mock_config = Mock()
        mock_config.resolve_config.side_effect = KeyError("config not found")
        mock_config_class.return_value = mock_config

        with pytest.raises(ValueError, match="Environment type not provided and no default env_type found"):
            EnvironmentManager.from_context(context)

    def test_switch_environment(self):
        """Test switch_environment method"""
        manager = EnvironmentManager(env_type="initial")
        assert manager._env_type == "initial"

        manager.switch_environment("new_env")
        assert manager._env_type == "new_env"
