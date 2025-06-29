"""Tests for OperationRepository."""
import pytest
from datetime import datetime
from unittest.mock import Mock, MagicMock

from src.data.operation.operation_repository import OperationRepository, Operation, PersistenceError


class TestOperationRepository:
    """Test suite for OperationRepository."""

    @pytest.fixture
    def mock_sqlite_manager(self):
        """Create a mock SQLite manager."""
        mock = Mock()
        mock.get_connection = MagicMock()
        mock.execute_query = Mock(return_value=[])
        mock.execute_command = Mock(return_value=1)
        return mock

    @pytest.fixture
    def mock_json_provider(self):
        """Create a mock JSON provider."""
        mock = Mock()
        mock.dumps = Mock(side_effect=lambda x: str(x) if x else None)
        mock.loads = Mock(side_effect=lambda x: eval(x) if x else None)
        return mock

    @pytest.fixture
    def repository(self, mock_sqlite_manager, mock_json_provider):
        """Create OperationRepository instance with mocks."""
        return OperationRepository(mock_sqlite_manager, mock_json_provider)

    @pytest.fixture
    def sample_operation(self):
        """Create a sample operation."""
        return Operation(
            id=None,
            timestamp=datetime(2024, 1, 1, 12, 0, 0),
            command="test",
            language="python",
            contest_name="contest1",
            problem_name="problemA",
            env_type="local",
            result="success",
            execution_time_ms=100,
            stdout="output",
            stderr="",
            return_code=0,
            details={"key": "value"},
            created_at=None
        )

    def test_initialization(self, mock_sqlite_manager, mock_json_provider):
        """Test repository initialization."""
        repo = OperationRepository(mock_sqlite_manager, mock_json_provider)
        assert repo.db_manager == mock_sqlite_manager
        assert repo._json_provider == mock_json_provider

    def test_serialize_details_with_data(self, repository, mock_json_provider):
        """Test details serialization with data."""
        details = {"key": "value", "number": 42}
        result = repository._serialize_details(details)
        mock_json_provider.dumps.assert_called_once_with(details)
        assert result == str(details)

    def test_serialize_details_with_none(self, repository, mock_json_provider):
        """Test details serialization with None."""
        result = repository._serialize_details(None)
        assert result is None
        mock_json_provider.dumps.assert_not_called()

    def test_create_entity_record_with_dict(self, repository, sample_operation):
        """Test create_entity_record with dictionary input."""
        entity_dict = {
            "id": None,
            "timestamp": datetime(2024, 1, 1, 12, 0, 0),
            "command": "test",
            "language": "python",
            "contest_name": "contest1",
            "problem_name": "problemA",
            "env_type": "local",
            "result": "success",
            "execution_time_ms": 100,
            "stdout": "output",
            "stderr": "",
            "return_code": 0,
            "details": {"key": "value"},
            "created_at": None
        }
        
        # Mock the find_by_id to return the created operation
        repository.find_by_id = Mock(return_value=sample_operation)
        
        # Mock the connection and cursor
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.lastrowid = 1
        mock_conn.execute.return_value = mock_cursor
        repository.db_manager.get_connection.return_value.__enter__.return_value = mock_conn
        
        result = repository.create_entity_record(entity_dict)
        
        # Verify the SQL query was executed
        mock_conn.execute.assert_called_once()
        assert "INSERT INTO operations" in mock_conn.execute.call_args[0][0]

    def test_create_operation_record(self, repository, sample_operation):
        """Test creating an operation record."""
        # Mock the connection and cursor
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.lastrowid = 1
        mock_conn.execute.return_value = mock_cursor
        repository.db_manager.get_connection.return_value.__enter__.return_value = mock_conn
        
        # Mock find_by_id to return the operation with ID
        created_operation = Operation(**sample_operation.__dict__)
        created_operation.id = 1
        repository.find_by_id = Mock(return_value=created_operation)
        
        result = repository.create_operation_record(sample_operation)
        
        assert result.id == 1
        repository.find_by_id.assert_called_once_with(1)

    def test_find_by_id_found(self, repository, mock_sqlite_manager):
        """Test finding operation by ID when found."""
        mock_row = {
            "id": 1,
            "timestamp": "2024-01-01T12:00:00",
            "command": "test",
            "language": "python",
            "contest_name": "contest1",
            "problem_name": "problemA",
            "env_type": "local",
            "result": "success",
            "execution_time_ms": 100,
            "stdout": "output",
            "stderr": "",
            "return_code": 0,
            "details": "{'key': 'value'}",
            "created_at": "2024-01-01T12:00:00"
        }
        mock_sqlite_manager.execute_query.return_value = [mock_row]
        
        result = repository.find_by_id(1)
        
        assert result is not None
        assert result.id == 1
        assert result.command == "test"
        mock_sqlite_manager.execute_query.assert_called_once_with(
            "SELECT * FROM operations WHERE id = ?", (1,)
        )

    def test_find_by_id_not_found(self, repository, mock_sqlite_manager):
        """Test finding operation by ID when not found."""
        mock_sqlite_manager.execute_query.return_value = []
        
        result = repository.find_by_id(999)
        
        assert result is None

    def test_find_all_with_pagination(self, repository, mock_sqlite_manager):
        """Test finding all operations with pagination."""
        mock_sqlite_manager.execute_query.return_value = []
        
        repository.find_all(limit=10, offset=5)
        
        expected_query = "SELECT * FROM operations ORDER BY timestamp DESC LIMIT ? OFFSET ?"
        mock_sqlite_manager.execute_query.assert_called_once_with(
            expected_query, (10, 5)
        )

    def test_find_all_no_pagination(self, repository, mock_sqlite_manager):
        """Test finding all operations without pagination."""
        mock_sqlite_manager.execute_query.return_value = []
        
        repository.find_all(limit=None, offset=None)
        
        expected_query = "SELECT * FROM operations ORDER BY timestamp DESC"
        mock_sqlite_manager.execute_query.assert_called_once_with(
            expected_query, ()
        )

    def test_find_by_command(self, repository, mock_sqlite_manager):
        """Test finding operations by command."""
        mock_sqlite_manager.execute_query.return_value = []
        
        repository.find_by_command("test", limit=5)
        
        expected_query = "SELECT * FROM operations WHERE command = ? ORDER BY timestamp DESC LIMIT ?"
        mock_sqlite_manager.execute_query.assert_called_once_with(
            expected_query, ("test", 5)
        )

    def test_find_by_contest_with_problem(self, repository, mock_sqlite_manager):
        """Test finding operations by contest and problem."""
        mock_sqlite_manager.execute_query.return_value = []
        
        repository.find_by_contest("contest1", "problemA")
        
        mock_sqlite_manager.execute_query.assert_called_once()
        args = mock_sqlite_manager.execute_query.call_args[0]
        assert "contest_name = ? AND problem_name = ?" in args[0]
        assert args[1] == ("contest1", "problemA")

    def test_find_by_contest_without_problem(self, repository, mock_sqlite_manager):
        """Test finding operations by contest only."""
        mock_sqlite_manager.execute_query.return_value = []
        
        repository.find_by_contest("contest1", None)
        
        mock_sqlite_manager.execute_query.assert_called_once()
        args = mock_sqlite_manager.execute_query.call_args[0]
        assert "contest_name = ?" in args[0]
        assert "problem_name" not in args[0]
        assert args[1] == ("contest1",)

    def test_find_by_language(self, repository, mock_sqlite_manager):
        """Test finding operations by language."""
        mock_sqlite_manager.execute_query.return_value = []
        
        repository.find_by_language("python", limit=10)
        
        expected_query = "SELECT * FROM operations WHERE language = ? ORDER BY timestamp DESC LIMIT ?"
        mock_sqlite_manager.execute_query.assert_called_once_with(
            expected_query, ("python", 10)
        )

    def test_get_recent_operations(self, repository):
        """Test getting recent operations."""
        repository.find_all = Mock(return_value=[])
        
        repository.get_recent_operations(5)
        
        repository.find_all.assert_called_once_with(limit=5)

    def test_get_statistics(self, repository, mock_sqlite_manager):
        """Test getting operation statistics."""
        # Mock the query results
        mock_sqlite_manager.execute_query.side_effect = [
            [{"count": 100}],  # total operations
            [{"count": 80}],   # successful operations
            [{"language": "python", "count": 50}, {"language": "cpp", "count": 30}],  # language stats
            [{"command": "test", "count": 60}, {"command": "submit", "count": 40}]   # command stats
        ]
        
        result = repository.get_statistics()
        
        assert result["total_operations"] == 100
        assert result["successful_operations"] == 80
        assert result["success_rate"] == 80.0
        assert len(result["language_usage"]) == 2
        assert len(result["command_usage"]) == 2

    def test_get_statistics_no_operations(self, repository, mock_sqlite_manager):
        """Test getting statistics when no operations exist."""
        mock_sqlite_manager.execute_query.return_value = [{"count": 0}]
        
        with pytest.raises(ValueError, match="Cannot calculate success rate"):
            repository.get_statistics()

    def test_update_operation(self, repository, sample_operation, mock_sqlite_manager):
        """Test updating an operation."""
        sample_operation.id = 1
        
        result = repository.update(sample_operation)
        
        assert result == sample_operation
        mock_sqlite_manager.execute_command.assert_called_once()
        args = mock_sqlite_manager.execute_command.call_args[0]
        assert "UPDATE operations SET" in args[0]
        assert args[1][-1] == 1  # ID should be last parameter

    def test_delete_operation_success(self, repository, mock_sqlite_manager):
        """Test deleting an operation successfully."""
        mock_sqlite_manager.execute_command.return_value = 1
        
        result = repository.delete(1)
        
        assert result is True
        mock_sqlite_manager.execute_command.assert_called_once_with(
            "DELETE FROM operations WHERE id = ?", (1,)
        )

    def test_delete_operation_not_found(self, repository, mock_sqlite_manager):
        """Test deleting a non-existent operation."""
        mock_sqlite_manager.execute_command.return_value = 0
        
        result = repository.delete(999)
        
        assert result is False

    def test_row_to_operation_with_details(self, repository):
        """Test converting database row to Operation with details."""
        row = {
            "id": 1,
            "timestamp": "2024-01-01T12:00:00",
            "command": "test",
            "language": "python",
            "contest_name": "contest1",
            "problem_name": "problemA",
            "env_type": "local",
            "result": "success",
            "execution_time_ms": 100,
            "stdout": "output",
            "stderr": "",
            "return_code": 0,
            "details": "{'key': 'value'}",
            "created_at": "2024-01-01T12:00:00"
        }
        
        result = repository._row_to_operation(row)
        
        assert result.id == 1
        assert result.command == "test"
        assert result.details == {'key': 'value'}

    def test_row_to_operation_json_error(self, repository, mock_json_provider):
        """Test row to operation conversion with JSON parsing error."""
        row = {
            "id": 1,
            "timestamp": "2024-01-01T12:00:00",
            "command": "test",
            "language": "python",
            "contest_name": "contest1",
            "problem_name": "problemA",
            "env_type": "local",
            "result": "success",
            "execution_time_ms": 100,
            "stdout": "output",
            "stderr": "",
            "return_code": 0,
            "details": "invalid json",
            "created_at": "2024-01-01T12:00:00"
        }
        
        mock_json_provider.loads.side_effect = Exception("JSON parsing error")
        
        with pytest.raises(PersistenceError, match="Operation details JSON parsing failed"):
            repository._row_to_operation(row)