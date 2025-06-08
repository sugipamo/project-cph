"""Tests for SessionRepository - session management functionality."""
import os
import tempfile
from datetime import datetime, timedelta

import pytest

from src.infrastructure.persistence.sqlite.repositories.session_repository import (
    Session,
    SessionRepository,
)
from src.infrastructure.persistence.sqlite.sqlite_manager import SQLiteManager


class TestSessionRepository:
    """Test SessionRepository functionality."""

    @pytest.fixture
    def temp_db_path(self):
        """Create temporary database file."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            temp_path = f.name
        yield temp_path
        if os.path.exists(temp_path):
            os.unlink(temp_path)

    @pytest.fixture
    def sqlite_manager(self, temp_db_path):
        """Create SQLiteManager with temporary database."""
        return SQLiteManager(temp_db_path)

    @pytest.fixture
    def session_repo(self, sqlite_manager):
        """Create SessionRepository."""
        return SessionRepository(sqlite_manager)

    @pytest.fixture
    def sample_session(self):
        """Create sample session for testing."""
        return Session(
            language="python",
            contest_name="abc123",
            problem_name="a",
            total_operations=5,
            successful_operations=4
        )

    def test_create_session(self, session_repo, sample_session):
        """Test creating a new session."""
        created_session = session_repo.create(sample_session)

        assert created_session.id is not None
        assert created_session.language == "python"
        assert created_session.contest_name == "abc123"
        assert created_session.problem_name == "a"
        assert created_session.total_operations == 5
        assert created_session.successful_operations == 4
        assert isinstance(created_session.session_start, datetime)
        assert created_session.session_end is None  # Should be None for active session

    def test_create_session_with_explicit_times(self, session_repo):
        """Test creating session with explicit start/end times."""
        start_time = datetime(2023, 1, 1, 10, 0, 0)
        end_time = datetime(2023, 1, 1, 12, 0, 0)

        session = Session(
            session_start=start_time,
            session_end=end_time,
            language="cpp"
        )

        created_session = session_repo.create(session)
        assert created_session.session_start == start_time
        assert created_session.session_end == end_time

    def test_find_by_id_existing(self, session_repo, sample_session):
        """Test finding session by existing ID."""
        created_session = session_repo.create(sample_session)
        found_session = session_repo.find_by_id(created_session.id)

        assert found_session is not None
        assert found_session.id == created_session.id
        assert found_session.language == sample_session.language
        assert found_session.contest_name == sample_session.contest_name

    def test_find_by_id_nonexistent(self, session_repo):
        """Test finding session by non-existent ID."""
        found_session = session_repo.find_by_id(99999)
        assert found_session is None

    def test_find_all_empty(self, session_repo):
        """Test finding all sessions when database is empty."""
        sessions = session_repo.find_all()
        assert sessions == []

    def test_find_all_with_data(self, session_repo):
        """Test finding all sessions with data."""
        # Create test sessions with different start times
        session1 = Session(language="python", session_start=datetime(2023, 1, 1, 10, 0, 0))
        session2 = Session(language="cpp", session_start=datetime(2023, 1, 1, 11, 0, 0))
        session3 = Session(language="java", session_start=datetime(2023, 1, 1, 12, 0, 0))

        session_repo.create(session1)
        session_repo.create(session2)
        session_repo.create(session3)

        sessions = session_repo.find_all()
        assert len(sessions) == 3
        # Should be ordered by session_start DESC (most recent first)
        assert sessions[0].language == "java"  # Last created
        assert sessions[1].language == "cpp"
        assert sessions[2].language == "python"

    def test_find_all_with_pagination(self, session_repo):
        """Test pagination in find_all."""
        # Create 5 sessions
        for i in range(5):
            session = Session(language=f"lang{i}")
            session_repo.create(session)

        # Test limit
        limited = session_repo.find_all(limit=3)
        assert len(limited) == 3

        # Test limit with offset
        offset_sessions = session_repo.find_all(limit=2, offset=2)
        assert len(offset_sessions) == 2

        # Test that offset works correctly
        all_sessions = session_repo.find_all()
        assert offset_sessions[0].id == all_sessions[2].id
        assert offset_sessions[1].id == all_sessions[3].id

    def test_find_active_session_none(self, session_repo):
        """Test finding active session when none exists."""
        active_session = session_repo.find_active_session()
        assert active_session is None

    def test_find_active_session_with_active(self, session_repo):
        """Test finding active session when one exists."""
        # Create an active session (no end time)
        session = Session(language="python")
        created_session = session_repo.create(session)

        active_session = session_repo.find_active_session()
        assert active_session is not None
        assert active_session.id == created_session.id
        assert active_session.session_end is None

    def test_find_active_session_with_ended_session(self, session_repo):
        """Test finding active session when only ended sessions exist."""
        # Create an ended session
        end_time = datetime.now()
        session = Session(language="python", session_end=end_time)
        session_repo.create(session)

        active_session = session_repo.find_active_session()
        assert active_session is None

    def test_start_new_session(self, session_repo):
        """Test starting a new session."""
        new_session = session_repo.start_new_session(
            language="python",
            contest_name="abc123",
            problem_name="a"
        )

        assert new_session.id is not None
        assert new_session.language == "python"
        assert new_session.contest_name == "abc123"
        assert new_session.problem_name == "a"
        assert new_session.session_end is None
        assert isinstance(new_session.session_start, datetime)

    def test_start_new_session_ends_previous(self, session_repo):
        """Test that starting new session ends previous active session."""
        # Start first session
        first_session = session_repo.start_new_session(language="python")
        assert first_session.session_end is None

        # Start second session
        second_session = session_repo.start_new_session(language="cpp")

        # Verify first session was ended
        updated_first = session_repo.find_by_id(first_session.id)
        assert updated_first.session_end is not None

        # Verify second session is active
        assert second_session.session_end is None
        active = session_repo.find_active_session()
        assert active.id == second_session.id

    def test_end_session(self, session_repo):
        """Test ending an active session."""
        # Create active session
        session = session_repo.start_new_session(language="python")
        assert session.session_end is None

        # End the session
        result = session_repo.end_session(session.id)
        assert result is True

        # Verify session was ended
        updated_session = session_repo.find_by_id(session.id)
        assert updated_session.session_end is not None

    def test_end_session_nonexistent(self, session_repo):
        """Test ending non-existent session."""
        result = session_repo.end_session(99999)
        assert result is False

    def test_end_session_already_ended(self, session_repo):
        """Test ending already ended session."""
        # Create and end session
        session = session_repo.start_new_session(language="python")
        session_repo.end_session(session.id)

        # Try to end again
        result = session_repo.end_session(session.id)
        assert result is False  # Should return False since session was already ended

    def test_update_session_stats(self, session_repo):
        """Test updating session statistics."""
        session = session_repo.start_new_session(language="python")

        # Update stats
        result = session_repo.update_session_stats(session.id, 10, 8)
        assert result is True

        # Verify stats were updated
        updated_session = session_repo.find_by_id(session.id)
        assert updated_session.total_operations == 10
        assert updated_session.successful_operations == 8

    def test_update_session_stats_nonexistent(self, session_repo):
        """Test updating stats for non-existent session."""
        result = session_repo.update_session_stats(99999, 10, 8)
        assert result is False

    def test_get_recent_sessions(self, session_repo):
        """Test getting recent sessions."""
        # Create sessions
        for i in range(15):
            session_repo.start_new_session(language=f"lang{i}")

        # Default limit is 10
        recent = session_repo.get_recent_sessions()
        assert len(recent) == 10

        # Custom limit
        recent_5 = session_repo.get_recent_sessions(limit=5)
        assert len(recent_5) == 5

    def test_get_session_statistics_empty(self, session_repo):
        """Test statistics on empty database."""
        stats = session_repo.get_session_statistics()

        assert stats["total_sessions"] == 0
        assert stats["average_duration_minutes"] == 0
        assert stats["language_sessions"] == []

    def test_get_session_statistics_with_data(self, session_repo):
        """Test statistics with data."""
        # Create test sessions with different languages and durations
        start1 = datetime(2023, 1, 1, 10, 0, 0)
        end1 = datetime(2023, 1, 1, 11, 0, 0)  # 60 minutes

        start2 = datetime(2023, 1, 1, 12, 0, 0)
        end2 = datetime(2023, 1, 1, 12, 30, 0)  # 30 minutes

        session1 = Session(language="python", session_start=start1, session_end=end1)
        session2 = Session(language="python", session_start=start2, session_end=end2)
        session3 = Session(language="cpp")  # Active session (no end time)

        session_repo.create(session1)
        session_repo.create(session2)
        session_repo.create(session3)

        stats = session_repo.get_session_statistics()

        assert stats["total_sessions"] == 3
        assert abs(stats["average_duration_minutes"] - 45.0) < 0.1  # (60 + 30) / 2 = 45

        # Check language sessions
        lang_sessions = stats["language_sessions"]
        assert len(lang_sessions) == 2
        assert lang_sessions[0]["language"] == "python"
        assert lang_sessions[0]["count"] == 2

    def test_update_session(self, session_repo, sample_session):
        """Test updating an existing session."""
        created_session = session_repo.create(sample_session)

        # Modify the session
        created_session.language = "cpp"
        created_session.total_operations = 10
        created_session.successful_operations = 9
        created_session.session_end = datetime.now()

        # Update it
        updated_session = session_repo.update(created_session)

        # Verify update
        assert updated_session.language == "cpp"
        assert updated_session.total_operations == 10
        assert updated_session.successful_operations == 9

        # Verify from database
        found_session = session_repo.find_by_id(created_session.id)
        assert found_session.language == "cpp"
        assert found_session.total_operations == 10
        assert found_session.successful_operations == 9

    def test_delete_session(self, session_repo, sample_session):
        """Test deleting a session."""
        created_session = session_repo.create(sample_session)
        session_id = created_session.id

        # Verify it exists
        assert session_repo.find_by_id(session_id) is not None

        # Delete it
        result = session_repo.delete(session_id)
        assert result is True

        # Verify it's gone
        assert session_repo.find_by_id(session_id) is None

    def test_delete_nonexistent_session(self, session_repo):
        """Test deleting non-existent session."""
        result = session_repo.delete(99999)
        assert result is False

    def test_datetime_handling(self, session_repo):
        """Test proper datetime serialization/deserialization."""
        start_time = datetime(2023, 5, 15, 14, 30, 45)
        end_time = datetime(2023, 5, 15, 16, 30, 45)

        session = Session(
            language="test",
            session_start=start_time,
            session_end=end_time
        )

        created_session = session_repo.create(session)
        found_session = session_repo.find_by_id(created_session.id)

        # Should preserve the timestamps
        assert found_session.session_start == start_time
        assert found_session.session_end == end_time

    def test_session_workflow_complete(self, session_repo):
        """Test complete session workflow."""
        # Start session
        session = session_repo.start_new_session(
            language="python",
            contest_name="abc123",
            problem_name="a"
        )

        # Verify it's active
        active = session_repo.find_active_session()
        assert active.id == session.id

        # Update stats multiple times (simulating operations)
        session_repo.update_session_stats(session.id, 5, 4)
        session_repo.update_session_stats(session.id, 10, 8)
        session_repo.update_session_stats(session.id, 15, 12)

        # Check current stats
        current = session_repo.find_by_id(session.id)
        assert current.total_operations == 15
        assert current.successful_operations == 12

        # End session
        session_repo.end_session(session.id)

        # Verify no active session
        active = session_repo.find_active_session()
        assert active is None

        # Verify ended session
        ended = session_repo.find_by_id(session.id)
        assert ended.session_end is not None
        assert ended.total_operations == 15
        assert ended.successful_operations == 12
