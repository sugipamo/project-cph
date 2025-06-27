"""Repository for operation history management."""
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Optional

from src.application.sqlite_manager import SQLiteManager
from src.data.base.base_repository import DatabaseRepositoryFoundation


class PersistenceError(Exception):
    """永続化システムのエラー"""
    pass


@dataclass
class Operation:
    """Operation data model."""
    id: Optional[int]
    timestamp: Optional[datetime]
    command: str
    language: Optional[str]
    contest_name: Optional[str]
    problem_name: Optional[str]
    env_type: Optional[str]
    result: Optional[str]
    execution_time_ms: Optional[int]
    stdout: Optional[str]
    stderr: Optional[str]
    return_code: Optional[int]
    details: Optional[dict[str, Any]]
    created_at: Optional[datetime]


class OperationRepository(DatabaseRepositoryFoundation):
    """Repository for managing operation history."""

    def __init__(self, db_manager: SQLiteManager, json_provider):
        """Initialize repository with database manager.

        Args:
            db_manager: SQLite database manager
            json_provider: JSON操作プロバイダー
        """
        self.db_manager = db_manager
        self._json_provider = json_provider

    def _serialize_details(self, details: Optional[dict[str, Any]]) -> Optional[str]:
        """Serialize details dictionary to JSON string."""
        if not details:
            return None

        return self._json_provider.dumps(details)

    def create_entity_record(self, entity: dict[str, Any]) -> Any:
        """Create method for RepositoryInterface compatibility.

        Args:
            entity: Operation data as dictionary

        Returns:
            Created operation
        """
        # Convert dict to Operation object if needed
        if isinstance(entity, dict):
            operation = Operation(**entity)
        else:
            operation = entity
        return self.create_operation_record(operation)

    def create_operation_record(self, operation: Operation) -> Operation:
        """Create a new operation record in the database.

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

        timestamp = operation.timestamp or datetime.now()
        params = (
            timestamp.isoformat() if timestamp else None,
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
            self._serialize_details(operation.details)
        )

        with self.db_manager.get_connection() as conn:
            cursor = conn.execute(query, params)
            last_id = cursor.lastrowid

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

    def find_all(self, limit: Optional[int], offset: Optional[int]) -> list[Operation]:
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

    def find_by_command(self, command: str, limit: Optional[int]) -> list[Operation]:
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

    def find_by_contest(self, contest_name: str, problem_name: Optional[str]) -> list[Operation]:
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

    def find_by_language(self, language: str, limit: Optional[int]) -> list[Operation]:
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

    def get_recent_operations(self, limit: int) -> list[Operation]:
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

        if total_ops == 0:
            raise ValueError("Cannot calculate success rate: no operations found")

        return {
            "total_operations": total_ops,
            "successful_operations": success_ops,
            "success_rate": success_ops / total_ops * 100,
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
            operation.timestamp.isoformat() if operation.timestamp else None,
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
            self._serialize_details(operation.details),
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
                details = self._json_provider.loads(row["details"])
            except Exception as e:
                raise PersistenceError(f"Operation details JSON parsing failed: {e}") from e

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
