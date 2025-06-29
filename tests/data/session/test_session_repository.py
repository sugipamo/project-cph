"""Tests for SessionRepository."""
import pytest
from datetime import datetime
from unittest.mock import Mock, MagicMock

from src.data.session.session_repository import SessionRepository, Session


class TestSessionRepository:
    """Test suite for SessionRepository."""

    @pytest.fixture
    def mock_sqlite_manager(self):
        """Create a mock SQLite manager."""
        mock = Mock()
        mock.get_connection = MagicMock()
        mock.execute_query = Mock(return_value=[])
        mock.execute_command = Mock(return_value=1)
        return mock

    @pytest.fixture
    def repository(self, mock_sqlite_manager):
        """Create SessionRepository instance with mocks."""
        return SessionRepository(mock_sqlite_manager)

    @pytest.fixture
    def sample_session(self):
        """Create a sample session."""
        return Session(
            id=None,
            session_start=datetime(2024, 1, 1, 10, 0, 0),
            session_end=None,
            language="python",
            contest_name="contest1",
            problem_name="problemA",
            total_operations=10,
            successful_operations=8,
            created_at=None,
            updated_at=None
        )

    def test_initialization(self, mock_sqlite_manager):
        """Test repository initialization."""
        repo = SessionRepository(mock_sqlite_manager)
        assert repo.db_manager == mock_sqlite_manager

    def test_create_session_record(self, repository, sample_session):
        """Test creating a session record."""
        # Mock the connection and cursor
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.lastrowid = 1
        mock_conn.execute.return_value = mock_cursor
        repository.db_manager.get_connection.return_value.__enter__.return_value = mock_conn
        
        # Mock find_by_id to return the session with ID
        created_session = Session(**sample_session.__dict__)
        created_session.id = 1
        repository.find_by_id = Mock(return_value=created_session)
        
        result = repository.create_session_record(sample_session)
        
        assert result.id == 1
        repository.find_by_id.assert_called_once_with(1)

    def test_create_session_record_no_start_time(self, repository):
        """Test creating a session without start time raises error."""
        session = Session(language="python")
        
        with pytest.raises(ValueError, match="Session start time is required"):
            repository.create_session_record(session)

    def test_create_entity_record_with_dict(self, repository, sample_session):
        """Test create_entity_record with dictionary input."""
        entity_dict = {
            "session_start": datetime(2024, 1, 1, 10, 0, 0),
            "language": "python",
            "contest_name": "contest1",
            "problem_name": "problemA",
            "total_operations": 10,
            "successful_operations": 8
        }
        
        # Mock the create_session_record
        repository.create_session_record = Mock(return_value=sample_session)
        
        result = repository.create_entity_record(entity_dict)
        
        repository.create_session_record.assert_called_once()
        # Check that a Session object was created from the dict
        call_args = repository.create_session_record.call_args[0][0]
        assert isinstance(call_args, Session)
        assert call_args.language == "python"

    def test_find_by_id_found(self, repository, mock_sqlite_manager):
        """Test finding session by ID when found."""
        mock_row = {
            "id": 1,
            "session_start": "2024-01-01T10:00:00",
            "session_end": "2024-01-01T11:00:00",
            "language": "python",
            "contest_name": "contest1",
            "problem_name": "problemA",
            "total_operations": 10,
            "successful_operations": 8,
            "created_at": "2024-01-01T10:00:00",
            "updated_at": "2024-01-01T11:00:00"
        }
        mock_sqlite_manager.execute_query.return_value = [mock_row]
        
        result = repository.find_by_id(1)
        
        assert result is not None
        assert result.id == 1
        assert result.language == "python"
        mock_sqlite_manager.execute_query.assert_called_once_with(
            "SELECT * FROM sessions WHERE id = ?", (1,)
        )

    def test_find_by_id_not_found(self, repository, mock_sqlite_manager):
        """Test finding session by ID when not found."""
        mock_sqlite_manager.execute_query.return_value = []
        
        result = repository.find_by_id(999)
        
        assert result is None

    def test_find_all_with_pagination(self, repository, mock_sqlite_manager):
        """Test finding all sessions with pagination."""
        mock_sqlite_manager.execute_query.return_value = []
        
        repository.find_all(limit=10, offset=5)
        
        expected_query = "SELECT * FROM sessions ORDER BY session_start DESC LIMIT ? OFFSET ?"
        mock_sqlite_manager.execute_query.assert_called_once_with(
            expected_query, (10, 5)
        )

    def test_find_active_session(self, repository, mock_sqlite_manager):
        """Test finding active session."""
        mock_row = {
            "id": 1,
            "session_start": "2024-01-01T10:00:00",
            "session_end": None,
            "language": "python",
            "contest_name": "contest1",
            "problem_name": "problemA",
            "total_operations": 5,
            "successful_operations": 4,
            "created_at": "2024-01-01T10:00:00",
            "updated_at": None
        }
        mock_sqlite_manager.execute_query.return_value = [mock_row]
        
        result = repository.find_active_session()
        
        assert result is not None
        assert result.id == 1
        assert result.session_end is None

    def test_start_new_session_with_active(self, repository):
        """Test starting a new session when there's an active session."""
        # Mock active session
        active_session = Session(id=1, session_start=datetime.now())
        repository.find_active_session = Mock(return_value=active_session)
        repository.end_session = Mock(return_value=True)
        repository.create_session_record = Mock(return_value=Session(id=2))
        
        result = repository.start_new_session("python", "contest2", "problemB")
        
        repository.find_active_session.assert_called_once()
        repository.end_session.assert_called_once_with(1)
        repository.create_session_record.assert_called_once()
        assert result.id == 2

    def test_start_new_session_no_active(self, repository):
        """Test starting a new session when there's no active session."""
        repository.find_active_session = Mock(return_value=None)
        repository.create_session_record = Mock(return_value=Session(id=1))
        
        result = repository.start_new_session("cpp", "contest1", "problemC")
        
        repository.find_active_session.assert_called_once()
        repository.create_session_record.assert_called_once()
        # Check the created session has the right properties
        call_args = repository.create_session_record.call_args[0][0]
        assert call_args.language == "cpp"
        assert call_args.contest_name == "contest1"
        assert call_args.problem_name == "problemC"

    def test_end_session(self, repository, mock_sqlite_manager):
        """Test ending a session."""
        mock_sqlite_manager.execute_command.return_value = 1
        
        result = repository.end_session(1)
        
        assert result is True
        mock_sqlite_manager.execute_command.assert_called_once()
        args = mock_sqlite_manager.execute_command.call_args[0]
        assert "UPDATE sessions" in args[0]
        assert "session_end = ?" in args[0]

    def test_update_session_stats(self, repository, mock_sqlite_manager):
        """Test updating session statistics."""
        mock_sqlite_manager.execute_command.return_value = 1
        
        result = repository.update_session_stats(1, 20, 18)
        
        assert result is True
        mock_sqlite_manager.execute_command.assert_called_once()
        args = mock_sqlite_manager.execute_command.call_args[0]
        assert "UPDATE sessions" in args[0]
        assert "total_operations = ?" in args[0]
        assert "successful_operations = ?" in args[0]
        assert args[1] == (20, 18, 1)

    def test_get_recent_sessions(self, repository):
        """Test getting recent sessions."""
        repository.find_all = Mock(return_value=[])
        
        repository.get_recent_sessions(5)
        
        repository.find_all.assert_called_once_with(5, None)

    def test_get_session_statistics(self, repository, mock_sqlite_manager):
        """Test getting session statistics."""
        # Mock the query results
        mock_sqlite_manager.execute_query.side_effect = [
            [{"count": 50}],  # total sessions
            [{"avg_minutes": 45.5}],  # average duration
            [{"language": "python", "count": 30}, {"language": "cpp", "count": 20}]  # language sessions
        ]
        
        result = repository.get_session_statistics()
        
        assert result["total_sessions"] == 50
        assert result["average_duration_minutes"] == 45.5
        assert len(result["language_sessions"]) == 2

    def test_get_session_statistics_no_completed(self, repository, mock_sqlite_manager):
        """Test getting statistics when no completed sessions."""
        mock_sqlite_manager.execute_query.side_effect = [
            [{"count": 1}],  # total sessions
            [{"avg_minutes": None}],  # no completed sessions
            []  # language sessions (would be called after the check)
        ]
        
        with pytest.raises(ValueError, match="No completed sessions found"):
            repository.get_session_statistics()

    def test_update_session(self, repository, sample_session, mock_sqlite_manager):
        """Test updating a session."""
        sample_session.id = 1
        sample_session.session_end = datetime(2024, 1, 1, 11, 0, 0)
        
        result = repository.update(sample_session)
        
        assert result == sample_session
        mock_sqlite_manager.execute_command.assert_called_once()
        args = mock_sqlite_manager.execute_command.call_args[0]
        assert "UPDATE sessions SET" in args[0]
        assert args[1][-1] == 1  # ID should be last parameter

    def test_delete_session(self, repository, mock_sqlite_manager):
        """Test deleting a session."""
        mock_sqlite_manager.execute_command.return_value = 1
        
        result = repository.delete(1)
        
        assert result is True
        mock_sqlite_manager.execute_command.assert_called_once_with(
            "DELETE FROM sessions WHERE id = ?", (1,)
        )

    def test_row_to_session(self, repository):
        """Test converting database row to Session."""
        row = {
            "id": 1,
            "session_start": "2024-01-01T10:00:00",
            "session_end": "2024-01-01T11:00:00",
            "language": "python",
            "contest_name": "contest1",
            "problem_name": "problemA",
            "total_operations": 10,
            "successful_operations": 8,
            "created_at": "2024-01-01T10:00:00",
            "updated_at": "2024-01-01T11:00:00"
        }
        
        result = repository._row_to_session(row)
        
        assert result.id == 1
        assert result.language == "python"
        assert result.total_operations == 10
        assert result.successful_operations == 8
        assert isinstance(result.session_start, datetime)
        assert isinstance(result.session_end, datetime)