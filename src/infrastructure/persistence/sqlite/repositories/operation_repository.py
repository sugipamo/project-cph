"""Repository for operation history management."""
import json
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Optional

from src.infrastructure.persistence.base.base_repository import BaseRepository
from src.infrastructure.persistence.sqlite.sqlite_manager import SQLiteManager


@dataclass
class Operation:
    """Operation data model."""
    id: Optional[int] = None
    timestamp: Optional[datetime] = None
    command: str = ""
    language: Optional[str] = None
    contest_name: Optional[str] = None
    problem_name: Optional[str] = None
    env_type: Optional[str] = None
    result: Optional[str] = None
    execution_time_ms: Optional[int] = None
    stdout: Optional[str] = None
    stderr: Optional[str] = None
    return_code: Optional[int] = None
    details: Optional[dict[str, Any]] = None
    created_at: Optional[datetime] = None


class OperationRepository(BaseRepository):
    """Repository for managing operation history."""

    def __init__(self, db_manager: SQLiteManager):
        """Initialize repository with database manager.

        Args:
            db_manager: SQLite database manager
        """
        self.db_manager = db_manager

    def create(self, operation: Operation) -> Operation:
        """Create a new operation record.

        Args:
            operation: Operation to create

        Returns:
            Created operation with ID
        """
        query = """
        INSERT INTO operations (
            timestamp, command, language, contest_name, problem_name,
            env_type, result, execution_time_ms, stdout, stderr,
            return_code, details
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """

        params = (
            operation.timestamp or datetime.now(),
            operation.command,
            operation.language,
            operation.contest_name,
            operation.problem_name,
            operation.env_type,
            operation.result,
            operation.execution_time_ms,
            operation.stdout,
            operation.stderr,
            operation.return_code,
            json.dumps(operation.details) if operation.details else None
        )

        self.db_manager.execute_command(query, params)

        # Get the created operation
        last_id = self.db_manager.get_last_insert_id("operations")
        if last_id:
            return self.find_by_id(last_id)

        return operation

    def find_by_id(self, operation_id: int) -> Optional[Operation]:
        """Find operation by ID.

        Args:
            operation_id: Operation ID

        Returns:
            Operation if found, None otherwise
        """
        query = "SELECT * FROM operations WHERE id = ?"
        results = self.db_manager.execute_query(query, (operation_id,))

        if results:
            return self._row_to_operation(results[0])
        return None

    def find_all(self, limit: Optional[int] = None, offset: Optional[int] = None) -> list[Operation]:
        """Find all operations with optional pagination.

        Args:
            limit: Maximum number of operations to return
            offset: Number of operations to skip

        Returns:
            List of operations
        """
        query = "SELECT * FROM operations ORDER BY timestamp DESC"
        params = ()

        if limit is not None:
            query += " LIMIT ?"
            params += (limit,)

            if offset is not None:
                query += " OFFSET ?"
                params += (offset,)

        results = self.db_manager.execute_query(query, params)
        return [self._row_to_operation(row) for row in results]

    def find_by_command(self, command: str, limit: Optional[int] = None) -> list[Operation]:
        """Find operations by command type.

        Args:
            command: Command to search for
            limit: Maximum number of results

        Returns:
            List of matching operations
        """
        query = "SELECT * FROM operations WHERE command = ? ORDER BY timestamp DESC"
        params = (command,)

        if limit is not None:
            query += " LIMIT ?"
            params += (limit,)

        results = self.db_manager.execute_query(query, params)
        return [self._row_to_operation(row) for row in results]

    def find_by_contest(self, contest_name: str, problem_name: Optional[str] = None) -> list[Operation]:
        """Find operations by contest and optional problem.

        Args:
            contest_name: Contest name
            problem_name: Problem name (optional)

        Returns:
            List of matching operations
        """
        if problem_name:
            query = """
            SELECT * FROM operations
            WHERE contest_name = ? AND problem_name = ?
            ORDER BY timestamp DESC
            """
            params = (contest_name, problem_name)
        else:
            query = """
            SELECT * FROM operations
            WHERE contest_name = ?
            ORDER BY timestamp DESC
            """
            params = (contest_name,)

        results = self.db_manager.execute_query(query, params)
        return [self._row_to_operation(row) for row in results]

    def find_by_language(self, language: str, limit: Optional[int] = None) -> list[Operation]:
        """Find operations by programming language.

        Args:
            language: Programming language
            limit: Maximum number of results

        Returns:
            List of matching operations
        """
        query = "SELECT * FROM operations WHERE language = ? ORDER BY timestamp DESC"
        params = (language,)

        if limit is not None:
            query += " LIMIT ?"
            params += (limit,)

        results = self.db_manager.execute_query(query, params)
        return [self._row_to_operation(row) for row in results]

    def get_recent_operations(self, limit: int = 10) -> list[Operation]:
        """Get recent operations.

        Args:
            limit: Number of recent operations to return

        Returns:
            List of recent operations
        """
        return self.find_all(limit=limit)

    def get_statistics(self) -> dict[str, Any]:
        """Get operation statistics.

        Returns:
            Dictionary containing various statistics
        """
        total_ops = self.db_manager.execute_query("SELECT COUNT(*) as count FROM operations")[0]["count"]

        success_ops = self.db_manager.execute_query(
            "SELECT COUNT(*) as count FROM operations WHERE result = 'success'"
        )[0]["count"]

        language_stats = self.db_manager.execute_query("""
            SELECT language, COUNT(*) as count
            FROM operations
            WHERE language IS NOT NULL
            GROUP BY language
            ORDER BY count DESC
        """)

        command_stats = self.db_manager.execute_query("""
            SELECT command, COUNT(*) as count
            FROM operations
            GROUP BY command
            ORDER BY count DESC
        """)

        return {
            "total_operations": total_ops,
            "successful_operations": success_ops,
            "success_rate": (success_ops / total_ops * 100) if total_ops > 0 else 0,
            "language_usage": language_stats,
            "command_usage": command_stats
        }

    def update(self, operation: Operation) -> Operation:
        """Update an existing operation.

        Args:
            operation: Operation to update

        Returns:
            Updated operation
        """
        query = """
        UPDATE operations SET
            timestamp = ?, command = ?, language = ?, contest_name = ?,
            problem_name = ?, env_type = ?, result = ?, execution_time_ms = ?,
            stdout = ?, stderr = ?, return_code = ?, details = ?
        WHERE id = ?
        """

        params = (
            operation.timestamp,
            operation.command,
            operation.language,
            operation.contest_name,
            operation.problem_name,
            operation.env_type,
            operation.result,
            operation.execution_time_ms,
            operation.stdout,
            operation.stderr,
            operation.return_code,
            json.dumps(operation.details) if operation.details else None,
            operation.id
        )

        self.db_manager.execute_command(query, params)
        return operation

    def delete(self, operation_id: int) -> bool:
        """Delete operation by ID.

        Args:
            operation_id: ID of operation to delete

        Returns:
            True if deleted, False if not found
        """
        query = "DELETE FROM operations WHERE id = ?"
        affected_rows = self.db_manager.execute_command(query, (operation_id,))
        return affected_rows > 0

    def _row_to_operation(self, row: dict[str, Any]) -> Operation:
        """Convert database row to Operation object.

        Args:
            row: Database row as dictionary

        Returns:
            Operation object
        """
        details = None
        if row["details"]:
            try:
                details = json.loads(row["details"])
            except json.JSONDecodeError:
                details = {"raw": row["details"]}

        return Operation(
            id=row["id"],
            timestamp=datetime.fromisoformat(row["timestamp"]) if row["timestamp"] else None,
            command=row["command"],
            language=row["language"],
            contest_name=row["contest_name"],
            problem_name=row["problem_name"],
            env_type=row["env_type"],
            result=row["result"],
            execution_time_ms=row["execution_time_ms"],
            stdout=row["stdout"],
            stderr=row["stderr"],
            return_code=row["return_code"],
            details=details,
            created_at=datetime.fromisoformat(row["created_at"]) if row["created_at"] else None
        )
