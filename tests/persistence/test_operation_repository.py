"""Test module for OperationRepository."""
from datetime import datetime
from unittest.mock import Mock

import pytest

from src.infrastructure.persistence.sqlite.repositories.operation_repository import (
    Operation,
    OperationRepository,
    PersistenceError,
)


class TestOperationRepository:
    """Test class for OperationRepository."""

    @pytest.fixture
    def mock_db_manager(self):
        """Create mock database manager."""
        mock_manager = Mock()
        mock_manager.get_connection.return_value.__enter__ = Mock()
        mock_manager.get_connection.return_value.__exit__ = Mock(return_value=False)
        return mock_manager

    @pytest.fixture
    def mock_json_provider(self):
        """Create mock JSON provider."""
        mock_provider = Mock()
        mock_provider.dumps.return_value = '{"key": "value"}'
        mock_provider.loads.return_value = {"key": "value"}
        return mock_provider

    @pytest.fixture
    def repository(self, mock_db_manager, mock_json_provider):
        """Create repository instance."""
        return OperationRepository(mock_db_manager, mock_json_provider)

    @pytest.fixture
    def sample_operation(self):
        """Create sample operation."""
        return Operation(
            id=None,
            timestamp=datetime(2024, 1, 1, 12, 0, 0),
            command="test",
            language="python",
            contest_name="test_contest",
            problem_name="problem_a",
            env_type="local",
            result="success",
            execution_time_ms=100,
            stdout="test output",
            stderr="",
            return_code=0,
            details={"test": "data"},
            created_at=None
        )

    def test_serialize_details_with_data(self, repository, mock_json_provider):
        """Test _serialize_details with data."""
        details = {"key": "value"}
        result = repository._serialize_details(details)

        mock_json_provider.dumps.assert_called_once_with(details)
        assert result == '{"key": "value"}'

    def test_serialize_details_with_none(self, repository):
        """Test _serialize_details with None."""
        result = repository._serialize_details(None)
        assert result is None

    def test_serialize_details_with_empty_dict(self, repository):
        """Test _serialize_details with empty dict."""
        result = repository._serialize_details({})
        assert result is None

    def test_create_entity_record_with_dict(self, repository, sample_operation):
        """Test create_entity_record with dictionary."""
        repository.find_by_id = Mock(return_value=sample_operation)

        cursor_mock = Mock()
        cursor_mock.lastrowid = 1
        connection_mock = Mock()
        connection_mock.execute.return_value = cursor_mock
        repository.db_manager.get_connection.return_value.__enter__.return_value = connection_mock

        operation_dict = {
            "timestamp": datetime(2024, 1, 1, 12, 0, 0),
            "command": "test",
            "language": "python",
            "contest_name": "test_contest",
            "problem_name": "problem_a",
            "env_type": "local",
            "result": "success",
            "execution_time_ms": 100,
            "stdout": "test output",
            "stderr": "",
            "return_code": 0,
            "details": {"test": "data"},
        }

        result = repository.create_entity_record(operation_dict)
        assert result == sample_operation

    def test_create_entity_record_with_operation_object(self, repository, sample_operation):
        """Test create_entity_record with Operation object."""
        repository.create_operation_record = Mock(return_value=sample_operation)

        result = repository.create_entity_record(sample_operation)
        repository.create_operation_record.assert_called_once_with(sample_operation)
        assert result == sample_operation

    def test_create_operation_record_success(self, repository, sample_operation):
        """Test create_operation_record success."""
        repository.find_by_id = Mock(return_value=sample_operation)

        cursor_mock = Mock()
        cursor_mock.lastrowid = 1
        connection_mock = Mock()
        connection_mock.execute.return_value = cursor_mock
        repository.db_manager.get_connection.return_value.__enter__.return_value = connection_mock

        result = repository.create_operation_record(sample_operation)

        repository.find_by_id.assert_called_once_with(1)
        assert result == sample_operation

    def test_create_operation_record_no_id(self, repository, sample_operation):
        """Test create_operation_record when no ID is returned."""
        cursor_mock = Mock()
        cursor_mock.lastrowid = None
        connection_mock = Mock()
        connection_mock.execute.return_value = cursor_mock
        repository.db_manager.get_connection.return_value.__enter__.return_value = connection_mock

        result = repository.create_operation_record(sample_operation)
        assert result == sample_operation

    def test_find_by_id_found(self, repository, sample_operation):
        """Test find_by_id when operation is found."""
        mock_row = {
            "id": 1,
            "timestamp": "2024-01-01T12:00:00",
            "command": "test",
            "language": "python",
            "contest_name": "test_contest",
            "problem_name": "problem_a",
            "env_type": "local",
            "result": "success",
            "execution_time_ms": 100,
            "stdout": "test output",
            "stderr": "",
            "return_code": 0,
            "details": '{"test": "data"}',
            "created_at": None
        }

        repository.db_manager.execute_query.return_value = [mock_row]
        repository._row_to_operation = Mock(return_value=sample_operation)

        result = repository.find_by_id(1)

        repository.db_manager.execute_query.assert_called_once_with(
            "SELECT * FROM operations WHERE id = ?", (1,)
        )
        repository._row_to_operation.assert_called_once_with(mock_row)
        assert result == sample_operation

    def test_find_by_id_not_found(self, repository):
        """Test find_by_id when operation is not found."""
        repository.db_manager.execute_query.return_value = []

        result = repository.find_by_id(1)
        assert result is None

    def test_find_all_no_pagination(self, repository, sample_operation):
        """Test find_all without pagination."""
        mock_row = {"id": 1}
        repository.db_manager.execute_query.return_value = [mock_row]
        repository._row_to_operation = Mock(return_value=sample_operation)

        result = repository.find_all(None, None)

        repository.db_manager.execute_query.assert_called_once_with(
            "SELECT * FROM operations ORDER BY timestamp DESC", ()
        )
        assert result == [sample_operation]

    def test_find_all_with_limit(self, repository, sample_operation):
        """Test find_all with limit."""
        mock_row = {"id": 1}
        repository.db_manager.execute_query.return_value = [mock_row]
        repository._row_to_operation = Mock(return_value=sample_operation)

        result = repository.find_all(10, None)

        repository.db_manager.execute_query.assert_called_once_with(
            "SELECT * FROM operations ORDER BY timestamp DESC LIMIT ?", (10,)
        )
        assert result == [sample_operation]

    def test_find_all_with_limit_and_offset(self, repository, sample_operation):
        """Test find_all with limit and offset."""
        mock_row = {"id": 1}
        repository.db_manager.execute_query.return_value = [mock_row]
        repository._row_to_operation = Mock(return_value=sample_operation)

        result = repository.find_all(10, 5)

        repository.db_manager.execute_query.assert_called_once_with(
            "SELECT * FROM operations ORDER BY timestamp DESC LIMIT ? OFFSET ?", (10, 5)
        )
        assert result == [sample_operation]

    def test_find_by_command(self, repository, sample_operation):
        """Test find_by_command."""
        mock_row = {"id": 1}
        repository.db_manager.execute_query.return_value = [mock_row]
        repository._row_to_operation = Mock(return_value=sample_operation)

        result = repository.find_by_command("test", 10)

        repository.db_manager.execute_query.assert_called_once_with(
            "SELECT * FROM operations WHERE command = ? ORDER BY timestamp DESC LIMIT ?",
            ("test", 10)
        )
        assert result == [sample_operation]

    def test_find_by_contest_with_problem(self, repository, sample_operation):
        """Test find_by_contest with problem name."""
        mock_row = {"id": 1}
        repository.db_manager.execute_query.return_value = [mock_row]
        repository._row_to_operation = Mock(return_value=sample_operation)

        result = repository.find_by_contest("contest1", "problem_a")

        repository.db_manager.execute_query.assert_called_once()
        call_args = repository.db_manager.execute_query.call_args
        assert "contest_name = ? AND problem_name = ?" in call_args[0][0]
        assert call_args[0][1] == ("contest1", "problem_a")
        assert result == [sample_operation]

    def test_find_by_contest_without_problem(self, repository, sample_operation):
        """Test find_by_contest without problem name."""
        mock_row = {"id": 1}
        repository.db_manager.execute_query.return_value = [mock_row]
        repository._row_to_operation = Mock(return_value=sample_operation)

        result = repository.find_by_contest("contest1", None)

        repository.db_manager.execute_query.assert_called_once()
        call_args = repository.db_manager.execute_query.call_args
        assert "contest_name = ?" in call_args[0][0]
        assert "AND problem_name" not in call_args[0][0]
        assert call_args[0][1] == ("contest1",)
        assert result == [sample_operation]

    def test_find_by_language(self, repository, sample_operation):
        """Test find_by_language."""
        mock_row = {"id": 1}
        repository.db_manager.execute_query.return_value = [mock_row]
        repository._row_to_operation = Mock(return_value=sample_operation)

        result = repository.find_by_language("python", 5)

        repository.db_manager.execute_query.assert_called_once_with(
            "SELECT * FROM operations WHERE language = ? ORDER BY timestamp DESC LIMIT ?",
            ("python", 5)
        )
        assert result == [sample_operation]

    def test_get_recent_operations(self, repository, sample_operation):
        """Test get_recent_operations."""
        repository.find_all = Mock(return_value=[sample_operation])

        result = repository.get_recent_operations(10)

        repository.find_all.assert_called_once_with(limit=10)
        assert result == [sample_operation]

    def test_get_statistics_success(self, repository):
        """Test get_statistics with data."""
        repository.db_manager.execute_query.side_effect = [
            [{"count": 100}],  # total_ops
            [{"count": 80}],   # success_ops
            [{"language": "python", "count": 50}],  # language_stats
            [{"command": "test", "count": 30}]      # command_stats
        ]

        result = repository.get_statistics()

        assert result["total_operations"] == 100
        assert result["successful_operations"] == 80
        assert result["success_rate"] == 80.0
        assert result["language_usage"] == [{"language": "python", "count": 50}]
        assert result["command_usage"] == [{"command": "test", "count": 30}]

    def test_get_statistics_no_operations(self, repository):
        """Test get_statistics with no operations."""
        repository.db_manager.execute_query.return_value = [{"count": 0}]

        with pytest.raises(ValueError, match="Cannot calculate success rate: no operations found"):
            repository.get_statistics()

    def test_update(self, repository, sample_operation):
        """Test update operation."""
        repository.db_manager.execute_command.return_value = 1
        sample_operation.id = 1

        result = repository.update(sample_operation)

        repository.db_manager.execute_command.assert_called_once()
        call_args = repository.db_manager.execute_command.call_args
        assert "UPDATE operations SET" in call_args[0][0]
        assert call_args[0][1][-1] == 1  # operation.id at the end
        assert result == sample_operation

    def test_delete_success(self, repository):
        """Test delete operation success."""
        repository.db_manager.execute_command.return_value = 1

        result = repository.delete(1)

        repository.db_manager.execute_command.assert_called_once_with(
            "DELETE FROM operations WHERE id = ?", (1,)
        )
        assert result is True

    def test_delete_not_found(self, repository):
        """Test delete operation not found."""
        repository.db_manager.execute_command.return_value = 0

        result = repository.delete(1)
        assert result is False

    def test_row_to_operation_success(self, repository, mock_json_provider):
        """Test _row_to_operation with valid data."""
        mock_json_provider.loads.return_value = {"test": "data"}

        mock_row = {
            "id": 1,
            "timestamp": "2024-01-01T12:00:00",
            "command": "test",
            "language": "python",
            "contest_name": "test_contest",
            "problem_name": "problem_a",
            "env_type": "local",
            "result": "success",
            "execution_time_ms": 100,
            "stdout": "test output",
            "stderr": "",
            "return_code": 0,
            "details": '{"test": "data"}',
            "created_at": "2024-01-01T12:00:00"
        }

        result = repository._row_to_operation(mock_row)

        assert result.id == 1
        assert result.command == "test"
        assert result.language == "python"
        assert result.details == {"test": "data"}

    def test_row_to_operation_no_details(self, repository):
        """Test _row_to_operation with no details."""
        mock_row = {
            "id": 1,
            "timestamp": "2024-01-01T12:00:00",
            "command": "test",
            "language": "python",
            "contest_name": "test_contest",
            "problem_name": "problem_a",
            "env_type": "local",
            "result": "success",
            "execution_time_ms": 100,
            "stdout": "test output",
            "stderr": "",
            "return_code": 0,
            "details": None,
            "created_at": None
        }

        result = repository._row_to_operation(mock_row)

        assert result.details is None
        assert result.created_at is None

    def test_row_to_operation_json_error(self, repository, mock_json_provider):
        """Test _row_to_operation with JSON parse error."""
        mock_row = {
            "id": 1,
            "timestamp": "2024-01-01T12:00:00",
            "command": "test",
            "language": "python",
            "contest_name": "test_contest",
            "problem_name": "problem_a",
            "env_type": "local",
            "result": "success",
            "execution_time_ms": 100,
            "stdout": "test output",
            "stderr": "",
            "return_code": 0,
            "details": "invalid json",
            "created_at": None
        }

        mock_json_provider.loads.side_effect = Exception("JSON parse error")

        with pytest.raises(PersistenceError, match="Operation details JSON parsing failed"):
            repository._row_to_operation(mock_row)


class TestOperation:
    """Test class for Operation dataclass."""

    def test_operation_creation(self):
        """Test Operation creation."""
        operation = Operation(
            id=1,
            timestamp=datetime(2024, 1, 1, 12, 0, 0),
            command="test",
            language="python",
            contest_name="test_contest",
            problem_name="problem_a",
            env_type="local",
            result="success",
            execution_time_ms=100,
            stdout="test output",
            stderr="",
            return_code=0,
            details={"test": "data"},
            created_at=datetime(2024, 1, 1, 12, 0, 0)
        )

        assert operation.id == 1
        assert operation.command == "test"
        assert operation.language == "python"
        assert operation.details == {"test": "data"}

    def test_operation_with_none_values(self):
        """Test Operation with None values."""
        operation = Operation(
            id=None,
            timestamp=None,
            command="test",
            language=None,
            contest_name=None,
            problem_name=None,
            env_type=None,
            result=None,
            execution_time_ms=None,
            stdout=None,
            stderr=None,
            return_code=None,
            details=None,
            created_at=None
        )

        assert operation.id is None
        assert operation.timestamp is None
        assert operation.command == "test"
        assert operation.details is None


class TestPersistenceError:
    """Test class for PersistenceError."""

    def test_persistence_error_creation(self):
        """Test PersistenceError creation."""
        error = PersistenceError("Test error message")
        assert str(error) == "Test error message"
        assert isinstance(error, Exception)
