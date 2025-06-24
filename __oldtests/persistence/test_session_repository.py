"""Test module for SessionRepository."""
from datetime import datetime
from unittest.mock import Mock

import pytest

from src.infrastructure.persistence.sqlite.repositories.session_repository import Session, SessionRepository


class TestSessionRepository:
    """Test class for SessionRepository."""

    @pytest.fixture
    def mock_db_manager(self):
        """Create mock database manager."""
        mock_manager = Mock()
        mock_manager.get_connection.return_value.__enter__ = Mock()
        mock_manager.get_connection.return_value.__exit__ = Mock(return_value=False)
        return mock_manager

    @pytest.fixture
    def repository(self, mock_db_manager):
        """Create repository instance."""
        return SessionRepository(mock_db_manager)

    @pytest.fixture
    def sample_session(self):
        """Create sample session."""
        return Session(
            id=1,
            session_start=datetime(2024, 1, 1, 12, 0, 0),
            session_end=datetime(2024, 1, 1, 13, 0, 0),
            language="python",
            contest_name="test_contest",
            problem_name="problem_a",
            total_operations=10,
            successful_operations=8,
            created_at=datetime(2024, 1, 1, 12, 0, 0),
            updated_at=datetime(2024, 1, 1, 13, 0, 0)
        )

    def test_create_session_record_success(self, repository, sample_session):
        """Test create_session_record success."""
        repository.find_by_id = Mock(return_value=sample_session)

        cursor_mock = Mock()
        cursor_mock.lastrowid = 1
        connection_mock = Mock()
        connection_mock.execute.return_value = cursor_mock
        repository.db_manager.get_connection.return_value.__enter__.return_value = connection_mock

        test_session = Session(
            session_start=datetime(2024, 1, 1, 12, 0, 0),
            language="python",
            contest_name="test_contest",
            problem_name="problem_a",
            total_operations=10,
            successful_operations=8
        )

        result = repository.create_session_record(test_session)

        repository.find_by_id.assert_called_once_with(1)
        assert result == sample_session

    def test_create_session_record_no_start_time(self, repository):
        """Test create_session_record with no start time."""
        test_session = Session(
            session_start=None,
            language="python"
        )

        with pytest.raises(ValueError, match="Session start time is required"):
            repository.create_session_record(test_session)

    def test_create_session_record_no_id_returned(self, repository):
        """Test create_session_record when no ID is returned."""
        cursor_mock = Mock()
        cursor_mock.lastrowid = None
        connection_mock = Mock()
        connection_mock.execute.return_value = cursor_mock
        repository.db_manager.get_connection.return_value.__enter__.return_value = connection_mock

        test_session = Session(
            session_start=datetime(2024, 1, 1, 12, 0, 0),
            language="python"
        )

        result = repository.create_session_record(test_session)
        assert result == test_session

    def test_create_entity_record_with_dict(self, repository, sample_session):
        """Test create_entity_record with dictionary."""
        repository.create_session_record = Mock(return_value=sample_session)

        session_dict = {
            "session_start": datetime(2024, 1, 1, 12, 0, 0),
            "language": "python",
            "contest_name": "test_contest",
            "problem_name": "problem_a",
            "total_operations": 10,
            "successful_operations": 8
        }

        result = repository.create_entity_record(session_dict)

        repository.create_session_record.assert_called_once()
        call_args = repository.create_session_record.call_args[0][0]
        assert isinstance(call_args, Session)
        assert call_args.language == "python"
        assert result == sample_session

    def test_create_entity_record_with_session_object(self, repository, sample_session):
        """Test create_entity_record with Session object."""
        repository.create_session_record = Mock(return_value=sample_session)

        result = repository.create_entity_record(sample_session)
        repository.create_session_record.assert_called_once_with(sample_session)
        assert result == sample_session

    def test_find_by_id_found(self, repository, sample_session):
        """Test find_by_id when session is found."""
        mock_row = {
            "id": 1,
            "session_start": "2024-01-01T12:00:00",
            "session_end": "2024-01-01T13:00:00",
            "language": "python",
            "contest_name": "test_contest",
            "problem_name": "problem_a",
            "total_operations": 10,
            "successful_operations": 8,
            "created_at": "2024-01-01T12:00:00",
            "updated_at": "2024-01-01T13:00:00"
        }

        repository.db_manager.execute_query.return_value = [mock_row]
        repository._row_to_session = Mock(return_value=sample_session)

        result = repository.find_by_id(1)

        repository.db_manager.execute_query.assert_called_once_with(
            "SELECT * FROM sessions WHERE id = ?", (1,)
        )
        repository._row_to_session.assert_called_once_with(mock_row)
        assert result == sample_session

    def test_find_by_id_not_found(self, repository):
        """Test find_by_id when session is not found."""
        repository.db_manager.execute_query.return_value = []

        result = repository.find_by_id(1)
        assert result is None

    def test_find_all_no_pagination(self, repository, sample_session):
        """Test find_all without pagination."""
        mock_row = {"id": 1}
        repository.db_manager.execute_query.return_value = [mock_row]
        repository._row_to_session = Mock(return_value=sample_session)

        result = repository.find_all(None, None)

        repository.db_manager.execute_query.assert_called_once_with(
            "SELECT * FROM sessions ORDER BY session_start DESC", ()
        )
        assert result == [sample_session]

    def test_find_all_with_limit_and_offset(self, repository, sample_session):
        """Test find_all with limit and offset."""
        mock_row = {"id": 1}
        repository.db_manager.execute_query.return_value = [mock_row]
        repository._row_to_session = Mock(return_value=sample_session)

        result = repository.find_all(10, 5)

        repository.db_manager.execute_query.assert_called_once_with(
            "SELECT * FROM sessions ORDER BY session_start DESC LIMIT ? OFFSET ?", (10, 5)
        )
        assert result == [sample_session]

    def test_find_active_session_found(self, repository, sample_session):
        """Test find_active_session when active session exists."""
        mock_row = {"id": 1}
        repository.db_manager.execute_query.return_value = [mock_row]
        repository._row_to_session = Mock(return_value=sample_session)

        result = repository.find_active_session()

        repository.db_manager.execute_query.assert_called_once_with(
            "SELECT * FROM sessions WHERE session_end IS NULL ORDER BY session_start DESC LIMIT 1"
        )
        assert result == sample_session

    def test_find_active_session_not_found(self, repository):
        """Test find_active_session when no active session exists."""
        repository.db_manager.execute_query.return_value = []

        result = repository.find_active_session()
        assert result is None

    def test_start_new_session_with_active_session(self, repository, sample_session):
        """Test start_new_session when there's an active session."""
        active_session = Session(id=1)
        repository.find_active_session = Mock(return_value=active_session)
        repository.end_session = Mock(return_value=True)
        repository.create_session_record = Mock(return_value=sample_session)

        result = repository.start_new_session("python", "contest1", "problem_a")

        repository.find_active_session.assert_called_once()
        repository.end_session.assert_called_once_with(1)
        repository.create_session_record.assert_called_once()

        call_args = repository.create_session_record.call_args[0][0]
        assert isinstance(call_args, Session)
        assert call_args.language == "python"
        assert call_args.contest_name == "contest1"
        assert call_args.problem_name == "problem_a"
        assert result == sample_session

    def test_start_new_session_no_active_session(self, repository, sample_session):
        """Test start_new_session when there's no active session."""
        repository.find_active_session = Mock(return_value=None)
        repository.end_session = Mock()
        repository.create_session_record = Mock(return_value=sample_session)

        result = repository.start_new_session("python", "contest1", "problem_a")

        repository.find_active_session.assert_called_once()
        repository.end_session.assert_not_called()
        repository.create_session_record.assert_called_once()
        assert result == sample_session

    def test_end_session_success(self, repository):
        """Test end_session success."""
        repository.db_manager.execute_command.return_value = 1

        result = repository.end_session(1)

        repository.db_manager.execute_command.assert_called_once()
        call_args = repository.db_manager.execute_command.call_args
        assert "UPDATE sessions" in call_args[0][0]
        assert "session_end = ?" in call_args[0][0]
        assert "WHERE id = ? AND session_end IS NULL" in call_args[0][0]
        assert call_args[0][1][1] == 1  # session_id
        assert result is True

    def test_end_session_not_found(self, repository):
        """Test end_session when session not found."""
        repository.db_manager.execute_command.return_value = 0

        result = repository.end_session(1)
        assert result is False

    def test_update_session_stats_success(self, repository):
        """Test update_session_stats success."""
        repository.db_manager.execute_command.return_value = 1

        result = repository.update_session_stats(1, 10, 8)

        repository.db_manager.execute_command.assert_called_once_with(
            """
        UPDATE sessions
        SET total_operations = ?, successful_operations = ?, updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
        """,
            (10, 8, 1)
        )
        assert result is True

    def test_update_session_stats_not_found(self, repository):
        """Test update_session_stats when session not found."""
        repository.db_manager.execute_command.return_value = 0

        result = repository.update_session_stats(1, 10, 8)
        assert result is False

    def test_get_recent_sessions(self, repository, sample_session):
        """Test get_recent_sessions."""
        repository.find_all = Mock(return_value=[sample_session])

        result = repository.get_recent_sessions(5)

        repository.find_all.assert_called_once_with(5, None)
        assert result == [sample_session]

    def test_get_session_statistics_success(self, repository):
        """Test get_session_statistics with data."""
        repository.db_manager.execute_query.side_effect = [
            [{"count": 10}],          # total_sessions
            [{"avg_minutes": 60.5}],  # avg_duration
            [{"language": "python", "count": 8}]  # language_sessions
        ]

        result = repository.get_session_statistics()

        assert result["total_sessions"] == 10
        assert result["average_duration_minutes"] == 60.5
        assert result["language_sessions"] == [{"language": "python", "count": 8}]

    def test_get_session_statistics_no_completed_sessions(self, repository):
        """Test get_session_statistics with no completed sessions."""
        repository.db_manager.execute_query.side_effect = [
            [{"count": 5}],            # total_sessions
            [{"avg_minutes": None}],   # avg_duration (no completed sessions)
            [{"language": "python", "count": 3}]
        ]

        with pytest.raises(ValueError, match="No completed sessions found to calculate average duration"):
            repository.get_session_statistics()

    def test_update(self, repository, sample_session):
        """Test update session."""
        repository.db_manager.execute_command.return_value = 1

        result = repository.update(sample_session)

        repository.db_manager.execute_command.assert_called_once()
        call_args = repository.db_manager.execute_command.call_args
        assert "UPDATE sessions SET" in call_args[0][0]
        assert call_args[0][1][-1] == sample_session.id  # session.id at the end
        assert result == sample_session

    def test_delete_success(self, repository):
        """Test delete session success."""
        repository.db_manager.execute_command.return_value = 1

        result = repository.delete(1)

        repository.db_manager.execute_command.assert_called_once_with(
            "DELETE FROM sessions WHERE id = ?", (1,)
        )
        assert result is True

    def test_delete_not_found(self, repository):
        """Test delete session not found."""
        repository.db_manager.execute_command.return_value = 0

        result = repository.delete(1)
        assert result is False

    def test_row_to_session_success(self, repository):
        """Test _row_to_session with valid data."""
        mock_row = {
            "id": 1,
            "session_start": "2024-01-01T12:00:00",
            "session_end": "2024-01-01T13:00:00",
            "language": "python",
            "contest_name": "test_contest",
            "problem_name": "problem_a",
            "total_operations": 10,
            "successful_operations": 8,
            "created_at": "2024-01-01T12:00:00",
            "updated_at": "2024-01-01T13:00:00"
        }

        result = repository._row_to_session(mock_row)

        assert result.id == 1
        assert result.language == "python"
        assert result.contest_name == "test_contest"
        assert result.total_operations == 10
        assert result.successful_operations == 8

    def test_row_to_session_with_nulls(self, repository):
        """Test _row_to_session with null values."""
        mock_row = {
            "id": 1,
            "session_start": "2024-01-01T12:00:00",
            "session_end": None,
            "language": None,
            "contest_name": None,
            "problem_name": None,
            "total_operations": 0,
            "successful_operations": 0,
            "created_at": None,
            "updated_at": None
        }

        result = repository._row_to_session(mock_row)

        assert result.id == 1
        assert result.session_end is None
        assert result.language is None
        assert result.contest_name is None
        assert result.created_at is None
        assert result.updated_at is None


class TestSession:
    """Test class for Session dataclass."""

    def test_session_creation_with_defaults(self):
        """Test Session creation with default values."""
        session = Session()

        assert session.id is None
        assert session.session_start is None
        assert session.session_end is None
        assert session.language is None
        assert session.contest_name is None
        assert session.problem_name is None
        assert session.total_operations == 0
        assert session.successful_operations == 0
        assert session.created_at is None
        assert session.updated_at is None

    def test_session_creation_with_values(self):
        """Test Session creation with specific values."""
        start_time = datetime(2024, 1, 1, 12, 0, 0)
        end_time = datetime(2024, 1, 1, 13, 0, 0)
        created_time = datetime(2024, 1, 1, 12, 0, 0)

        session = Session(
            id=1,
            session_start=start_time,
            session_end=end_time,
            language="python",
            contest_name="test_contest",
            problem_name="problem_a",
            total_operations=10,
            successful_operations=8,
            created_at=created_time,
            updated_at=created_time
        )

        assert session.id == 1
        assert session.session_start == start_time
        assert session.session_end == end_time
        assert session.language == "python"
        assert session.contest_name == "test_contest"
        assert session.problem_name == "problem_a"
        assert session.total_operations == 10
        assert session.successful_operations == 8
        assert session.created_at == created_time
        assert session.updated_at == created_time

    def test_session_partial_initialization(self):
        """Test Session with partial initialization."""
        session = Session(
            language="java",
            contest_name="abc123"
        )

        assert session.id is None
        assert session.language == "java"
        assert session.contest_name == "abc123"
        assert session.total_operations == 0  # default value
        assert session.successful_operations == 0  # default value
