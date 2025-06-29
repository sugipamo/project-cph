"""Tests for EnvironmentManager."""
import pytest
from unittest.mock import Mock, MagicMock

from src.configuration.environment_manager import EnvironmentManager
from src.operations.results.result import OperationResult


class TestEnvironmentManager:
    """Test EnvironmentManager functionality."""

    @pytest.fixture
    def mock_logger(self):
        """Create mock logger."""
        return Mock()

    @pytest.fixture
    def mock_config_provider(self):
        """Create mock config provider."""
        provider = Mock()
        provider.resolve_config = Mock(return_value="local")
        provider.load_from_files = Mock()
        return provider

    def test_init_with_env_type(self, mock_config_provider, mock_logger):
        """Test initialization with explicit env_type."""
        manager = EnvironmentManager("docker", mock_config_provider, mock_logger)
        assert manager._env_type == "docker"
        assert manager._config_provider == mock_config_provider
        assert manager.logger == mock_logger

    def test_init_without_env_type(self, mock_config_provider, mock_logger):
        """Test initialization without env_type, loading from config."""
        manager = EnvironmentManager(None, mock_config_provider, mock_logger)
        assert manager._env_type == "local"
        mock_config_provider.load_from_files.assert_called_once_with(
            system_dir="./config/system",
            env_dir="./contest_env",
            language="python"
        )
        mock_config_provider.resolve_config.assert_called_once_with(
            ['env_default', 'env_type'], str
        )

    def test_init_config_error(self, mock_config_provider, mock_logger):
        """Test initialization error when config not found."""
        mock_config_provider.resolve_config.side_effect = KeyError("env_type not found")
        
        with pytest.raises(ValueError) as exc_info:
            EnvironmentManager(None, mock_config_provider, mock_logger)
        
        assert "Environment type not provided" in str(exc_info.value)

    def test_prepare_environment(self, mock_config_provider, mock_logger):
        """Test prepare_environment method."""
        manager = EnvironmentManager("local", mock_config_provider, mock_logger)
        context = Mock()
        
        result = manager.prepare_environment(context)
        
        assert isinstance(result, OperationResult)
        assert result.is_success() is True
        assert result.get_message() == "Environment local prepared"
        assert result.get_details()['operation'] == "prepare_environment"

    def test_cleanup_environment(self, mock_config_provider, mock_logger):
        """Test cleanup_environment method."""
        manager = EnvironmentManager("docker", mock_config_provider, mock_logger)
        context = Mock()
        
        result = manager.cleanup_environment(context)
        
        assert isinstance(result, OperationResult)
        assert result.is_success() is True
        assert result.get_message() == "Environment docker cleaned up"
        assert result.get_details()['operation'] == "cleanup_environment"

    def test_execute_request(self, mock_config_provider, mock_logger):
        """Test execute_request method."""
        manager = EnvironmentManager("local", mock_config_provider, mock_logger)
        
        mock_request = Mock()
        mock_driver = Mock()
        expected_result = Mock(spec=OperationResult)
        mock_request.execute_operation.return_value = expected_result
        
        result = manager.execute_request(mock_request, mock_driver)
        
        assert result == expected_result
        mock_request.execute_operation.assert_called_once_with(mock_driver, mock_logger)

    def test_should_force_local_with_force_env_type(self, mock_config_provider, mock_logger):
        """Test should_force_local with force_env_type=local."""
        manager = EnvironmentManager("docker", mock_config_provider, mock_logger)
        
        step_config = {"force_env_type": "local"}
        assert manager.should_force_local(step_config) is True
        
        step_config = {"force_env_type": "docker"}
        assert manager.should_force_local(step_config) is False

    def test_should_force_local_with_force_local(self, mock_config_provider, mock_logger):
        """Test should_force_local with legacy force_local field."""
        manager = EnvironmentManager("docker", mock_config_provider, mock_logger)
        
        step_config = {"force_local": True}
        assert manager.should_force_local(step_config) is True
        
        step_config = {"force_local": False}
        assert manager.should_force_local(step_config) is False

    def test_should_force_local_with_local_env(self, mock_config_provider, mock_logger):
        """Test should_force_local when current env is local."""
        manager = EnvironmentManager("local", mock_config_provider, mock_logger)
        
        step_config = {}
        assert manager.should_force_local(step_config) is True

    def test_get_working_directory(self, mock_config_provider, mock_logger):
        """Test get_working_directory method."""
        manager = EnvironmentManager("local", mock_config_provider, mock_logger)
        assert manager.get_working_directory() == "."

    def test_get_timeout(self, mock_config_provider, mock_logger):
        """Test get_timeout method."""
        manager = EnvironmentManager("local", mock_config_provider, mock_logger)
        assert manager.get_timeout() == 300

    def test_get_shell(self, mock_config_provider, mock_logger):
        """Test get_shell method."""
        manager = EnvironmentManager("local", mock_config_provider, mock_logger)
        assert manager.get_shell() == "bash"

    def test_get_workspace_root(self, mock_config_provider, mock_logger):
        """Test get_workspace_root method."""
        manager = EnvironmentManager("local", mock_config_provider, mock_logger)
        assert manager.get_workspace_root() == "./workspace"

    def test_from_context_with_env_type(self, mock_config_provider, mock_logger):
        """Test from_context class method with env_type in context."""
        context = Mock(env_type="docker")
        
        manager = EnvironmentManager.from_context(context, mock_config_provider, mock_logger)
        
        assert manager._env_type == "docker"

    def test_from_context_without_env_type(self, mock_config_provider, mock_logger):
        """Test from_context class method without env_type in context."""
        context = Mock(spec=[])  # No env_type attribute
        
        manager = EnvironmentManager.from_context(context, mock_config_provider, mock_logger)
        
        # Should use None and load from config
        assert manager._env_type == "local"

    def test_switch_environment(self, mock_config_provider, mock_logger):
        """Test switch_environment method."""
        manager = EnvironmentManager("local", mock_config_provider, mock_logger)
        
        manager.switch_environment("docker")
        assert manager._env_type == "docker"
        
        manager.switch_environment("local")
        assert manager._env_type == "local"