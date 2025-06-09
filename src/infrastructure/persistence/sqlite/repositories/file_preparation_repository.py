"""Repository for managing file preparation operations tracking."""

from typing import List, Optional

from src.infrastructure.persistence.base.base_repository import BaseRepository


class FilePreparationRepository(BaseRepository):
    """Repository for tracking file preparation operations like test file movements."""

    def __init__(self, db_manager):
        """Initialize repository with database manager.

        Args:
            db_manager: SQLite database manager
        """
        self.db_manager = db_manager

    def create(self, entity: dict) -> int:
        """Create a new file preparation operation record."""
        return self.record_operation(**entity)

    def find_by_id(self, entity_id: int) -> Optional[dict]:
        """Find a file preparation operation by ID."""
        query = "SELECT * FROM file_preparation_operations WHERE id = ?"
        with self.db_manager.get_connection() as conn:
            cursor = conn.execute(query, (entity_id,))
            row = cursor.fetchone()

        if row:
            return {
                'id': row[0],
                'language_name': row[1],
                'contest_name': row[2],
                'problem_name': row[3],
                'operation_type': row[4],
                'source_path': row[5],
                'destination_path': row[6],
                'file_count': row[7],
                'success': bool(row[8]),
                'error_message': row[9],
                'created_at': row[10]
            }
        return None

    def find_all(self) -> List[dict]:
        """Find all file preparation operations."""
        query = "SELECT * FROM file_preparation_operations ORDER BY created_at DESC"
        with self.db_manager.get_connection() as conn:
            cursor = conn.execute(query)
            rows = cursor.fetchall()

        return [
            {
                'id': row[0],
                'language_name': row[1],
                'contest_name': row[2],
                'problem_name': row[3],
                'operation_type': row[4],
                'source_path': row[5],
                'destination_path': row[6],
                'file_count': row[7],
                'success': bool(row[8]),
                'error_message': row[9],
                'created_at': row[10]
            }
            for row in rows
        ]

    def update(self, entity_id: int, entity: dict) -> bool:
        """Update a file preparation operation record."""
        query = """
        UPDATE file_preparation_operations
        SET success = ?, error_message = ?, file_count = ?
        WHERE id = ?
        """
        with self.db_manager.get_connection() as conn:
            cursor = conn.execute(
                query,
                (entity.get('success', True), entity.get('error_message'),
                 entity.get('file_count', 0), entity_id)
            )
            return cursor.rowcount > 0

    def delete(self, entity_id: int) -> bool:
        """Delete a file preparation operation record."""
        query = "DELETE FROM file_preparation_operations WHERE id = ?"
        with self.db_manager.get_connection() as conn:
            cursor = conn.execute(query, (entity_id,))
            return cursor.rowcount > 0

    def record_operation(
        self,
        language_name: str,
        contest_name: str,
        problem_name: str,
        operation_type: str,
        source_path: str,
        destination_path: str,
        file_count: int = 0,
        success: bool = True,
        error_message: Optional[str] = None
    ) -> int:
        """Record a file preparation operation.

        Args:
            language_name: Programming language name
            contest_name: Contest identifier
            problem_name: Problem identifier
            operation_type: Type of operation (e.g., 'move_test_files')
            source_path: Source file/directory path
            destination_path: Destination file/directory path
            file_count: Number of files processed
            success: Whether operation was successful
            error_message: Error message if operation failed

        Returns:
            Operation ID
        """
        query = """
        INSERT OR REPLACE INTO file_preparation_operations
        (language_name, contest_name, problem_name, operation_type,
         source_path, destination_path, file_count, success, error_message)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """

        with self.db_manager.get_connection() as conn:
            cursor = conn.execute(
                query,
                (language_name, contest_name, problem_name, operation_type,
                 source_path, destination_path, file_count, success, error_message)
            )
            return cursor.lastrowid

    def get_operations_by_context(
        self,
        language_name: str,
        contest_name: str,
        problem_name: str
    ) -> List[dict]:
        """Get all file preparation operations for a specific contest context.

        Args:
            language_name: Programming language name
            contest_name: Contest identifier
            problem_name: Problem identifier

        Returns:
            List of operation records
        """
        query = """
        SELECT id, operation_type, source_path, destination_path,
               file_count, success, error_message, created_at
        FROM file_preparation_operations
        WHERE language_name = ? AND contest_name = ? AND problem_name = ?
        ORDER BY created_at DESC
        """

        with self.db_manager.get_connection() as conn:
            cursor = conn.execute(query, (language_name, contest_name, problem_name))
            rows = cursor.fetchall()

        return [
            {
                'id': row[0],
                'operation_type': row[1],
                'source_path': row[2],
                'destination_path': row[3],
                'file_count': row[4],
                'success': bool(row[5]),
                'error_message': row[6],
                'created_at': row[7]
            }
            for row in rows
        ]

    def get_latest_operation(
        self,
        language_name: str,
        contest_name: str,
        problem_name: str,
        operation_type: str
    ) -> Optional[dict]:
        """Get the latest operation of a specific type for a contest context.

        Args:
            language_name: Programming language name
            contest_name: Contest identifier
            problem_name: Problem identifier
            operation_type: Type of operation to find

        Returns:
            Latest operation record or None
        """
        query = """
        SELECT id, source_path, destination_path, file_count,
               success, error_message, created_at
        FROM file_preparation_operations
        WHERE language_name = ? AND contest_name = ? AND problem_name = ?
              AND operation_type = ?
        ORDER BY created_at DESC
        LIMIT 1
        """

        with self.db_manager.get_connection() as conn:
            cursor = conn.execute(
                query, (language_name, contest_name, problem_name, operation_type)
            )
            row = cursor.fetchone()

        if row:
            return {
                'id': row[0],
                'source_path': row[1],
                'destination_path': row[2],
                'file_count': row[3],
                'success': bool(row[4]),
                'error_message': row[5],
                'created_at': row[6]
            }
        return None

    def has_successful_operation(
        self,
        language_name: str,
        contest_name: str,
        problem_name: str,
        operation_type: str
    ) -> bool:
        """Check if there's a successful operation of a specific type.

        Args:
            language_name: Programming language name
            contest_name: Contest identifier
            problem_name: Problem identifier
            operation_type: Type of operation to check

        Returns:
            True if successful operation exists
        """
        query = """
        SELECT COUNT(*) FROM file_preparation_operations
        WHERE language_name = ? AND contest_name = ? AND problem_name = ?
              AND operation_type = ? AND success = 1
        """

        with self.db_manager.get_connection() as conn:
            cursor = conn.execute(
                query, (language_name, contest_name, problem_name, operation_type)
            )
            count = cursor.fetchone()[0]
            return count > 0

    def cleanup_old_operations(self, days: int = 30) -> int:
        """Clean up operations older than specified days.

        Args:
            days: Number of days to keep

        Returns:
            Number of deleted records
        """
        query = f"""
        DELETE FROM file_preparation_operations
        WHERE created_at < datetime('now', '-{days} days')
        """

        with self.db_manager.get_connection() as conn:
            cursor = conn.execute(query)
            return cursor.rowcount
