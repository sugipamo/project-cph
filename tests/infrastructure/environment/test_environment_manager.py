"""Tests for EnvironmentManager"""

from unittest.mock import MagicMock, Mock

import pytest

from src.infrastructure.environment.environment_manager import EnvironmentManager
from src.operations.requests.base.base_request import OperationRequestFoundation
from src.operations.results.result import OperationResult


class TestEnvironmentManager:
    """Tests for EnvironmentManager class"""

    def test_init_default_env_type(self):
        """Test initialization with default environment type"""
        manager = EnvironmentManager()
        assert manager._env_type == "local"

    def test_init_custom_env_type(self):
        """Test initialization with custom environment type"""
        manager = EnvironmentManager("docker")
        assert manager._env_type == "docker"

    def test_init_none_env_type(self):
        """Test initialization with None environment type falls back to local"""
        manager = EnvironmentManager(None)
        assert manager._env_type == "local"

    def test_prepare_environment(self):
        """Test environment preparation"""
        manager = EnvironmentManager("docker")
        context = Mock()

        result = manager.prepare_environment(context)

        assert isinstance(result, OperationResult)
        assert result.success is True
        assert "Environment docker prepared" in result.error_message

    def test_cleanup_environment(self):
        """Test environment cleanup"""
        manager = EnvironmentManager("local")
        context = Mock()

        result = manager.cleanup_environment(context)

        assert isinstance(result, OperationResult)
        assert result.success is True
        assert "Environment local cleaned up" in result.error_message

    def test_execute_request(self):
        """Test request execution"""
        manager = EnvironmentManager()
        mock_request = Mock(spec=OperationRequestFoundation)
        mock_driver = Mock()
        expected_result = OperationResult(success=True, error_message="Test result")
        mock_request.execute_operation.return_value = expected_result

        result = manager.execute_request(mock_request, mock_driver)

        assert result == expected_result
        mock_request.execute_operation.assert_called_once_with(mock_driver)

    def test_should_force_local_with_force_env_type_local(self):
        """Test should_force_local when force_env_type is set to local"""
        manager = EnvironmentManager("docker")
        step_config = {"force_env_type": "local"}

        result = manager.should_force_local(step_config)

        assert result is True

    def test_should_force_local_with_force_env_type_docker(self):
        """Test should_force_local when force_env_type is set to docker"""
        manager = EnvironmentManager("local")
        step_config = {"force_env_type": "docker"}

        result = manager.should_force_local(step_config)

        assert result is True  # Still True because manager env_type is local

    def test_should_force_local_with_force_local_true(self):
        """Test should_force_local with force_local set to True"""
        manager = EnvironmentManager("docker")
        step_config = {"force_local": True}

        result = manager.should_force_local(step_config)

        assert result is True

    def test_should_force_local_with_force_local_false(self):
        """Test should_force_local with force_local set to False"""
        manager = EnvironmentManager("docker")
        step_config = {"force_local": False}

        result = manager.should_force_local(step_config)

        assert result is False

    def test_should_force_local_with_empty_config(self):
        """Test should_force_local with empty configuration"""
        manager = EnvironmentManager("docker")
        step_config = {}

        result = manager.should_force_local(step_config)

        assert result is False

    def test_should_force_local_with_local_env_type(self):
        """Test should_force_local when manager env_type is local"""
        manager = EnvironmentManager("local")
        step_config = {}

        result = manager.should_force_local(step_config)

        assert result is True

    def test_get_working_directory(self):
        """Test get_working_directory returns current directory"""
        manager = EnvironmentManager()

        result = manager.get_working_directory()

        assert result == "."

    def test_get_timeout(self):
        """Test get_timeout returns default timeout"""
        manager = EnvironmentManager()

        result = manager.get_timeout()

        assert result == 300

    def test_get_shell(self):
        """Test get_shell returns bash"""
        manager = EnvironmentManager()

        result = manager.get_shell()

        assert result == "bash"

    def test_get_workspace_root(self):
        """Test get_workspace_root returns workspace directory"""
        manager = EnvironmentManager()

        result = manager.get_workspace_root()

        assert result == "./workspace"

    def test_from_context_with_env_type(self):
        """Test from_context class method with env_type"""
        context = Mock()
        context.env_type = "docker"

        manager = EnvironmentManager.from_context(context)

        assert isinstance(manager, EnvironmentManager)
        assert manager._env_type == "docker"

    def test_from_context_without_env_type(self):
        """Test from_context class method without env_type attribute"""
        context = Mock()
        # Don't set env_type attribute
        del context.env_type  # Remove if exists

        manager = EnvironmentManager.from_context(context)

        assert isinstance(manager, EnvironmentManager)
        assert manager._env_type == "local"

    def test_from_context_with_none_env_type(self):
        """Test from_context class method with None env_type"""
        context = Mock()
        context.env_type = None

        manager = EnvironmentManager.from_context(context)

        assert isinstance(manager, EnvironmentManager)
        assert manager._env_type == "local"

    def test_switch_environment(self):
        """Test switch_environment method"""
        manager = EnvironmentManager("local")
        assert manager._env_type == "local"

        manager.switch_environment("docker")

        assert manager._env_type == "docker"

    def test_switch_environment_multiple_times(self):
        """Test switching environment multiple times"""
        manager = EnvironmentManager("local")

        manager.switch_environment("docker")
        assert manager._env_type == "docker"

        manager.switch_environment("kubernetes")
        assert manager._env_type == "kubernetes"

        manager.switch_environment("local")
        assert manager._env_type == "local"

    def test_environment_manager_state_consistency(self):
        """Test that environment manager maintains consistent state"""
        manager = EnvironmentManager("docker")

        # Test that all methods work consistently with the set environment
        assert manager._env_type == "docker"

        prepare_result = manager.prepare_environment(Mock())
        assert "docker" in prepare_result.error_message

        cleanup_result = manager.cleanup_environment(Mock())
        assert "docker" in cleanup_result.error_message

        # Force local should be False for docker environment with empty config
        assert manager.should_force_local({}) is False
