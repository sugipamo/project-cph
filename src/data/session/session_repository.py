"""Repository for session management."""
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, Optional

from src.data.base.base_repository import DatabaseRepositoryFoundation
from src.application.sqlite_manager import SQLiteManager


@dataclass
class Session:
    """Session data model."""
    id: Optional[int] = None
    session_start: Optional[datetime] = None
    session_end: Optional[datetime] = None
    language: Optional[str] = None
    contest_name: Optional[str] = None
    problem_name: Optional[str] = None
    total_operations: int = 0
    successful_operations: int = 0
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class SessionRepository(DatabaseRepositoryFoundation):
    """Repository for managing work sessions."""

    def __init__(self, db_manager: SQLiteManager):
        """Initialize repository with database manager.

        Args:
            db_manager: SQLite database manager
        """
        self.db_manager = db_manager

    def create_session_record(self, session: Session) -> Session:
        """Create a new session record.

        Args:
            session: Session to create

        Returns:
            Created session with ID
        """
        query = """
        INSERT INTO sessions (
            session_start, session_end, language, contest_name, problem_name,
            total_operations, successful_operations
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """

        if session.session_start is None:
            raise ValueError("Session start time is required")
        session_start = session.session_start
        params = (
            session_start.isoformat() if session_start else None,
            session.session_end.isoformat() if session.session_end else None,
            session.language,
            session.contest_name,
            session.problem_name,
            session.total_operations,
            session.successful_operations
        )

        with self.db_manager.get_connection() as conn:
            cursor = conn.execute(query, params)
            last_id = cursor.lastrowid

        if last_id:
            return self.find_by_id(last_id)

        return session

    def create_entity_record(self, entity: Dict[str, Any]) -> Any:
        """Create method for RepositoryInterface compatibility.

        Args:
            entity: Session data as dictionary

        Returns:
            Created session
        """
        # Convert dict to Session object if needed
        if isinstance(entity, dict):
            session = Session(**entity)
        else:
            session = entity
        return self.create_session_record(session)


    def find_by_id(self, session_id: int) -> Optional[Session]:
        """Find session by ID.

        Args:
            session_id: Session ID

        Returns:
            Session if found, None otherwise
        """
        query = "SELECT * FROM sessions WHERE id = ?"
        results = self.db_manager.execute_query(query, (session_id,))

        if results:
            return self._row_to_session(results[0])
        return None

    def find_all(self, limit: Optional[int], offset: Optional[int]) -> list[Session]:
        """Find all sessions with optional pagination.

        Args:
            limit: Maximum number of sessions to return
            offset: Number of sessions to skip

        Returns:
            List of sessions
        """
        query = "SELECT * FROM sessions ORDER BY session_start DESC"
        params = ()

        if limit is not None:
            query += " LIMIT ?"
            params += (limit,)

            if offset is not None:
                query += " OFFSET ?"
                params += (offset,)

        results = self.db_manager.execute_query(query, params)
        return [self._row_to_session(row) for row in results]

    def find_active_session(self) -> Optional[Session]:
        """Find the current active session (session_end is NULL).

        Returns:
            Active session if found, None otherwise
        """
        query = "SELECT * FROM sessions WHERE session_end IS NULL ORDER BY session_start DESC LIMIT 1"
        results = self.db_manager.execute_query(query)

        if results:
            return self._row_to_session(results[0])
        return None

    def start_new_session(self, language: Optional[str],
                         contest_name: Optional[str],
                         problem_name: Optional[str]) -> Session:
        """Start a new session, ending any active session first.

        Args:
            language: Programming language for this session
            contest_name: Contest name
            problem_name: Problem name

        Returns:
            New session
        """
        # End any active session
        active_session = self.find_active_session()
        if active_session:
            self.end_session(active_session.id)

        # Create new session
        new_session = Session(
            session_start=datetime.now(),
            language=language,
            contest_name=contest_name,
            problem_name=problem_name
        )

        return self.create_session_record(new_session)

    def end_session(self, session_id: int) -> bool:
        """End a session by setting session_end timestamp.

        Args:
            session_id: ID of session to end

        Returns:
            True if session was ended, False otherwise
        """
        query = """
        UPDATE sessions
        SET session_end = ?, updated_at = CURRENT_TIMESTAMP
        WHERE id = ? AND session_end IS NULL
        """

        affected_rows = self.db_manager.execute_command(query, (datetime.now().isoformat(), session_id))
        return affected_rows > 0

    def update_session_stats(self, session_id: int, total_ops: int, successful_ops: int) -> bool:
        """Update session operation statistics.

        Args:
            session_id: Session ID
            total_ops: Total number of operations
            successful_ops: Number of successful operations

        Returns:
            True if updated, False otherwise
        """
        query = """
        UPDATE sessions
        SET total_operations = ?, successful_operations = ?, updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
        """

        affected_rows = self.db_manager.execute_command(query, (total_ops, successful_ops, session_id))
        return affected_rows > 0

    def get_recent_sessions(self, limit: int) -> list[Session]:
        """Get recent sessions.

        Args:
            limit: Number of recent sessions to return

        Returns:
            List of recent sessions
        """
        return self.find_all(limit, None)

    def get_session_statistics(self) -> dict[str, Any]:
        """Get session statistics.

        Returns:
            Dictionary containing session statistics
        """
        total_sessions = self.db_manager.execute_query("SELECT COUNT(*) as count FROM sessions")[0]["count"]

        avg_duration = self.db_manager.execute_query("""
            SELECT AVG(
                (julianday(session_end) - julianday(session_start)) * 24 * 60
            ) as avg_minutes
            FROM sessions
            WHERE session_end IS NOT NULL
        """)[0]["avg_minutes"]

        language_sessions = self.db_manager.execute_query("""
            SELECT language, COUNT(*) as count
            FROM sessions
            WHERE language IS NOT NULL
            GROUP BY language
            ORDER BY count DESC
        """)

        if avg_duration is None:
            raise ValueError("No completed sessions found to calculate average duration")

        return {
            "total_sessions": total_sessions,
            "average_duration_minutes": avg_duration,
            "language_sessions": language_sessions
        }

    def update(self, session: Session) -> Session:
        """Update an existing session.

        Args:
            session: Session to update

        Returns:
            Updated session
        """
        query = """
        UPDATE sessions SET
            session_start = ?, session_end = ?, language = ?, contest_name = ?,
            problem_name = ?, total_operations = ?, successful_operations = ?,
            updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
        """

        params = (
            session.session_start.isoformat() if session.session_start else None,
            session.session_end.isoformat() if session.session_end else None,
            session.language,
            session.contest_name,
            session.problem_name,
            session.total_operations,
            session.successful_operations,
            session.id
        )

        self.db_manager.execute_command(query, params)
        return session

    def delete(self, session_id: int) -> bool:
        """Delete session by ID.

        Args:
            session_id: ID of session to delete

        Returns:
            True if deleted, False if not found
        """
        query = "DELETE FROM sessions WHERE id = ?"
        affected_rows = self.db_manager.execute_command(query, (session_id,))
        return affected_rows > 0

    def _row_to_session(self, row: dict[str, Any]) -> Session:
        """Convert database row to Session object.

        Args:
            row: Database row as dictionary

        Returns:
            Session object
        """
        return Session(
            id=row["id"],
            session_start=datetime.fromisoformat(row["session_start"]) if row["session_start"] else None,
            session_end=datetime.fromisoformat(row["session_end"]) if row["session_end"] else None,
            language=row["language"],
            contest_name=row["contest_name"],
            problem_name=row["problem_name"],
            total_operations=row["total_operations"],
            successful_operations=row["successful_operations"],
            created_at=datetime.fromisoformat(row["created_at"]) if row["created_at"] else None,
            updated_at=datetime.fromisoformat(row["updated_at"]) if row["updated_at"] else None
        )
