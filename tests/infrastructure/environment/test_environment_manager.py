"""Tests for EnvironmentManager"""

from unittest.mock import Mock, patch

import pytest

from src.configuration.config_manager import TypeSafeConfigNodeManager
from src.infrastructure.environment.environment_manager import EnvironmentManager
from src.operations.requests.base.base_request import OperationRequestFoundation
from src.operations.results.result import OperationResult


class TestEnvironmentManager:
    """Tests for EnvironmentManager class"""

    def test_init_with_env_type(self, mock_infrastructure):
        """Test initialization with explicit env_type"""
        config_manager = mock_infrastructure.resolve('config_manager')
        logger = mock_infrastructure.resolve('logger')
        manager = EnvironmentManager(env_type="docker", config_manager=config_manager, logger=logger)
        assert manager._env_type == "docker"

    def test_init_with_config_manager(self, mock_infrastructure):
        """Test initialization with explicit config manager"""
        config_manager = mock_infrastructure.resolve('config_manager')
        logger = mock_infrastructure.resolve('logger')
        manager = EnvironmentManager(env_type="local", config_manager=config_manager, logger=logger)
        assert manager._config_manager == config_manager
        assert manager._env_type == "local"

    def test_init_loads_config_when_no_env_type(self, mock_infrastructure):
        """Test initialization loads config when env_type not provided"""
        config_manager = Mock(spec=TypeSafeConfigNodeManager)
        config_manager.resolve_config.return_value = "test_env"

        logger = Mock()
        manager = EnvironmentManager(env_type=None, config_manager=config_manager, logger=logger)

        config_manager.load_from_files.assert_called_once_with(system_dir="./config/system", env_dir="./contest_env", language="python")
        config_manager.resolve_config.assert_called_once_with(['env_default', 'env_type'], str)
        assert manager._env_type == "test_env"


    def test_prepare_environment(self, mock_infrastructure):
        """Test prepare_environment method"""
        config_manager = mock_infrastructure.resolve('config_manager')
        logger = mock_infrastructure.resolve('logger')
        manager = EnvironmentManager(env_type="test", config_manager=config_manager, logger=logger)
        context = Mock()

        result = manager.prepare_environment(context)

        assert isinstance(result, OperationResult)
        assert result.success is True
        assert "Environment test prepared" in result.error_message

    def test_cleanup_environment(self, mock_infrastructure):
        """Test cleanup_environment method"""
        config_manager = mock_infrastructure.resolve('config_manager')
        logger = mock_infrastructure.resolve('logger')
        manager = EnvironmentManager(env_type="test", config_manager=config_manager, logger=logger)
        context = Mock()

        result = manager.cleanup_environment(context)

        assert isinstance(result, OperationResult)
        assert result.success is True
        assert "Environment test cleaned up" in result.error_message

    def test_execute_request(self, mock_infrastructure):
        """Test execute_request method"""
        config_manager = mock_infrastructure.resolve('config_manager')
        logger = mock_infrastructure.resolve('logger')
        manager = EnvironmentManager(env_type="test", config_manager=config_manager, logger=logger)
        request = Mock(spec=OperationRequestFoundation)
        driver = Mock()
        expected_result = Mock(spec=OperationResult)
        request.execute_operation.return_value = expected_result

        result = manager.execute_request(request, driver)

        request.execute_operation.assert_called_once_with(driver, logger)
        assert result == expected_result

    def test_should_force_local_with_force_env_type_local(self, mock_infrastructure):
        """Test should_force_local returns True when force_env_type is local"""
        config_manager = mock_infrastructure.resolve('config_manager')
        logger = mock_infrastructure.resolve('logger')
        manager = EnvironmentManager(env_type="docker", config_manager=config_manager, logger=logger)
        step_config = {"force_env_type": "local"}

        assert manager.should_force_local(step_config) is True

    def test_should_force_local_with_force_env_type_docker(self, mock_infrastructure):
        """Test should_force_local returns False when force_env_type is docker and env_type is not local"""
        config_manager = mock_infrastructure.resolve('config_manager')
        logger = mock_infrastructure.resolve('logger')
        manager = EnvironmentManager(env_type="docker", config_manager=config_manager, logger=logger)
        step_config = {"force_env_type": "docker"}

        assert manager.should_force_local(step_config) is False

    def test_should_force_local_with_force_local_true(self, mock_infrastructure):
        """Test should_force_local returns True when force_local is True (backwards compatibility)"""
        config_manager = mock_infrastructure.resolve('config_manager')
        logger = mock_infrastructure.resolve('logger')
        manager = EnvironmentManager(env_type="docker", config_manager=config_manager, logger=logger)
        step_config = {"force_local": True}

        assert manager.should_force_local(step_config) is True

    def test_should_force_local_with_force_local_false(self, mock_infrastructure):
        """Test should_force_local returns False when force_local is False"""
        config_manager = mock_infrastructure.resolve('config_manager')
        logger = mock_infrastructure.resolve('logger')
        manager = EnvironmentManager(env_type="docker", config_manager=config_manager, logger=logger)
        step_config = {"force_local": False}

        assert manager.should_force_local(step_config) is False

    def test_should_force_local_with_local_env_type(self, mock_infrastructure):
        """Test should_force_local returns True when env_type is local"""
        config_manager = mock_infrastructure.resolve('config_manager')
        logger = mock_infrastructure.resolve('logger')
        manager = EnvironmentManager(env_type="local", config_manager=config_manager, logger=logger)
        step_config = {}

        assert manager.should_force_local(step_config) is True

    def test_should_force_local_with_non_local_env_type(self, mock_infrastructure):
        """Test should_force_local returns False when env_type is not local"""
        config_manager = mock_infrastructure.resolve('config_manager')
        logger = mock_infrastructure.resolve('logger')
        manager = EnvironmentManager(env_type="docker", config_manager=config_manager, logger=logger)
        step_config = {}

        assert manager.should_force_local(step_config) is False

    def test_get_working_directory(self, mock_infrastructure):
        """Test get_working_directory method"""
        config_manager = mock_infrastructure.resolve('config_manager')
        logger = mock_infrastructure.resolve('logger')
        manager = EnvironmentManager(env_type="test", config_manager=config_manager, logger=logger)
        assert manager.get_working_directory() == "."

    def test_get_timeout(self, mock_infrastructure):
        """Test get_timeout method"""
        config_manager = mock_infrastructure.resolve('config_manager')
        logger = mock_infrastructure.resolve('logger')
        manager = EnvironmentManager(env_type="test", config_manager=config_manager, logger=logger)
        assert manager.get_timeout() == 300

    def test_get_shell(self, mock_infrastructure):
        """Test get_shell method"""
        config_manager = mock_infrastructure.resolve('config_manager')
        logger = mock_infrastructure.resolve('logger')
        manager = EnvironmentManager(env_type="test", config_manager=config_manager, logger=logger)
        assert manager.get_shell() == "bash"

    def test_get_workspace_root(self, mock_infrastructure):
        """Test get_workspace_root method"""
        config_manager = mock_infrastructure.resolve('config_manager')
        logger = mock_infrastructure.resolve('logger')
        manager = EnvironmentManager(env_type="test", config_manager=config_manager, logger=logger)
        assert manager.get_workspace_root() == "./workspace"

    def test_from_context_with_env_type(self, mock_infrastructure):
        """Test from_context class method with env_type"""
        context = Mock()
        context.env_type = "test_env"
        config_manager = mock_infrastructure.resolve('config_manager')

        logger = mock_infrastructure.resolve('logger')
        manager = EnvironmentManager.from_context(context, config_manager, logger)

        assert manager._env_type == "test_env"


    def test_switch_environment(self, mock_infrastructure):
        """Test switch_environment method"""
        config_manager = mock_infrastructure.resolve('config_manager')
        logger = mock_infrastructure.resolve('logger')
        manager = EnvironmentManager(env_type="initial", config_manager=config_manager, logger=logger)
        assert manager._env_type == "initial"

        manager.switch_environment("new_env")
        assert manager._env_type == "new_env"
