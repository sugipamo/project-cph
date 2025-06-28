"""Tests for SqliteStateRepository

Testing the SQLite-based state management implementation
"""
import pytest
from unittest.mock import Mock, MagicMock, patch
from datetime import datetime

from src.data.sqlite_state.sqlite_state_repository import SqliteStateRepository
from src.application.execution_history import ExecutionHistory
from src.infrastructure.persistence.state.models.session_context import SessionContext
from src.configuration.system_config_repository import SystemConfigRepository


class MockConfig:
    """Mock configuration object"""
    def __init__(self, key, value, category=None):
        self.key = key
        self.value = value
        self.category = category
        # Also support dict-like access for compatibility
        self.config_key = key
        self.config_value = value


class TestSqliteStateRepository:
    """Tests for SqliteStateRepository"""

    @pytest.fixture
    def mock_config_repo(self):
        """Create a mock SystemConfigRepository"""
        return Mock(spec=SystemConfigRepository)

    @pytest.fixture
    def mock_json_provider(self):
        """Create a mock JSON provider"""
        provider = Mock()
        provider.dumps = Mock(return_value="mocked_json_string")
        provider.loads = Mock(side_effect=eval)
        return provider

    @pytest.fixture
    def repository(self, mock_config_repo, mock_json_provider):
        """Create a SqliteStateRepository instance"""
        return SqliteStateRepository(mock_config_repo, mock_json_provider)

    def test_save_execution_history(self, repository, mock_config_repo, mock_json_provider):
        """Test saving execution history"""
        # Arrange
        history = ExecutionHistory(
            contest_name="abc123",
            problem_name="A",
            language="python",
            env_type="docker",
            timestamp="2025-06-28T12:00:00",
            success=True
        )

        # Act
        repository.save_execution_history(history)

        # Assert
        mock_json_provider.dumps.assert_called_once()
        mock_config_repo.set_config.assert_called_once_with(
            key="history_2025-06-28T12:00:00",
            value="mocked_json_string",
            category='execution_history',
            description='Execution history for abc123_A'
        )

    def test_get_execution_history(self, repository, mock_config_repo, mock_json_provider):
        """Test retrieving execution history"""
        # Arrange
        # get_configs_by_category returns list of dicts
        mock_configs = [
            {
                'config_key': 'history_2025-06-28T12:00:00',
                'config_value': "{'contest_name': 'abc123', 'problem_name': 'A', 'language': 'python', 'env_type': 'docker', 'timestamp': '2025-06-28T12:00:00', 'success': True}",
                'category': 'execution_history'
            },
            {
                'config_key': 'history_2025-06-28T11:00:00',
                'config_value': "{'contest_name': 'abc122', 'problem_name': 'B', 'language': 'cpp', 'env_type': 'local', 'timestamp': '2025-06-28T11:00:00', 'success': False}",
                'category': 'execution_history'
            }
        ]
        mock_config_repo.get_configs_by_category.return_value = mock_configs

        # Act
        histories = repository.get_execution_history(limit=10)

        # Assert
        assert len(histories) == 2
        assert histories[0].contest_name == 'abc123'
        assert histories[0].success is True
        assert histories[1].contest_name == 'abc122'
        assert histories[1].success is False

    def test_get_execution_history_with_invalid_data(self, repository, mock_config_repo, mock_json_provider):
        """Test retrieving execution history with invalid data"""
        # Arrange
        mock_configs = [
            {
                'config_key': 'history_2025-06-28T12:00:00',
                'config_value': "invalid json",
                'category': 'execution_history'
            }
        ]
        mock_config_repo.get_configs_by_category.return_value = mock_configs
        mock_json_provider.loads.side_effect = ValueError("Invalid JSON")

        # Act
        histories = repository.get_execution_history(limit=10)

        # Assert
        assert len(histories) == 0

    def test_save_session_context(self, repository, mock_config_repo, mock_json_provider):
        """Test saving session context"""
        # Arrange
        context = SessionContext(
            current_contest="abc123",
            current_problem="A",
            current_language="python",
            previous_contest="abc122",
            previous_problem="B",
            user_specified_fields={"timeout": 30}
        )

        # Act
        repository.save_session_context(context)

        # Assert
        mock_json_provider.dumps.assert_called_once()
        mock_config_repo.set_config.assert_called_once_with(
            key='current_session',
            value="mocked_json_string",
            category='session_state',
            description='Current session context'
        )

    def test_load_session_context(self, repository, mock_config_repo, mock_json_provider):
        """Test loading session context"""
        # Arrange
        # get_config returns the value directly, not a config object
        mock_config_repo.get_config.return_value = "{'current_contest': 'abc123', 'current_problem': 'A', 'current_language': 'python', 'previous_contest': 'abc122', 'previous_problem': 'B', 'user_specified_fields': {'timeout': 30}}"

        # Act
        context = repository.load_session_context()

        # Assert
        assert context is not None
        assert context.current_contest == 'abc123'
        assert context.current_problem == 'A'
        assert context.user_specified_fields == {'timeout': 30}

    def test_load_session_context_none(self, repository, mock_config_repo):
        """Test loading session context when none exists"""
        # Arrange
        mock_config_repo.get_config.return_value = None

        # Act
        context = repository.load_session_context()

        # Assert
        assert context is None

    def test_save_user_specified_values(self, repository, mock_config_repo, mock_json_provider):
        """Test saving user specified values"""
        # Arrange
        values = {"timeout": 30, "memory_limit": 256}

        # Act
        repository.save_user_specified_values(values)

        # Assert
        mock_json_provider.dumps.assert_called_once_with(values)
        mock_config_repo.set_config.assert_called_once_with(
            key='user_values',
            value="mocked_json_string",
            category='user_specified',
            description='User specified values'
        )

    def test_get_user_specified_values(self, repository, mock_config_repo, mock_json_provider):
        """Test retrieving user specified values"""
        # Arrange
        # get_config returns the value directly
        mock_config_repo.get_config.return_value = "{'timeout': 30, 'memory_limit': 256}"

        # Act
        values = repository.get_user_specified_values()

        # Assert
        assert values == {'timeout': 30, 'memory_limit': 256}

    def test_get_user_specified_values_empty(self, repository, mock_config_repo):
        """Test retrieving user specified values when none exist"""
        # Arrange
        mock_config_repo.get_config.return_value = None

        # Act
        values = repository.get_user_specified_values()

        # Assert
        assert values == {}

    def test_clear_session(self, repository, mock_config_repo):
        """Test clearing session data"""
        # Arrange
        mock_configs = [
            {'config_key': 'session_1', 'config_value': 'data1', 'category': 'session_state'},
            {'config_key': 'session_2', 'config_value': 'data2', 'category': 'session_state'}
        ]
        mock_config_repo.get_configs_by_category.return_value = mock_configs

        # Act
        repository.clear_session()

        # Assert
        assert mock_config_repo.delete_config.call_count == 2
        mock_config_repo.delete_config.assert_any_call('session_1')
        mock_config_repo.delete_config.assert_any_call('session_2')