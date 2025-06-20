"""Persistence-specific exceptions."""
from typing import Optional


class PersistenceError(Exception):
    """Base exception for persistence operations."""

    def __init__(self, message: str, operation: Optional[str] = None, details: Optional[dict] = None):
        """Initialize persistence error.

        Args:
            message: Error message
            operation: Operation that failed (e.g., 'query', 'insert', 'update')
            details: Additional error details
        """
        super().__init__(message)
        self.operation = operation
        if details is None:
            self.details = {}
        else:
            self.details = details


class ConnectionError(PersistenceError):
    """Exception raised when database connection fails."""

    def __init__(self, message: str = "Database connection failed", **kwargs):
        super().__init__(message, operation="connection", **kwargs)


class MigrationError(PersistenceError):
    """Exception raised when database migration fails."""

    def __init__(self, message: str, migration_version: Optional[int] = None, **kwargs):
        super().__init__(message, operation="migration", **kwargs)
        self.migration_version = migration_version


class QueryError(PersistenceError):
    """Exception raised when SQL query execution fails."""

    def __init__(self, message: str, query: Optional[str] = None, params: Optional[tuple] = None, **kwargs):
        super().__init__(message, operation="query", **kwargs)
        self.query = query
        self.params = params


class TransactionError(PersistenceError):
    """Exception raised when transaction operations fail."""

    def __init__(self, message: str = "Transaction failed", **kwargs):
        super().__init__(message, operation="transaction", **kwargs)


class RepositoryError(PersistenceError):
    """Exception raised when repository operations fail."""

    def __init__(self, message: str, repository_name: Optional[str] = None, entity_id: Optional[str] = None, **kwargs):
        super().__init__(message, operation="repository", **kwargs)
        self.repository_name = repository_name
        self.entity_id = entity_id


class IntegrityError(PersistenceError):
    """Exception raised when data integrity constraints are violated."""

    def __init__(self, message: str, constraint: Optional[str] = None, **kwargs):
        super().__init__(message, operation="integrity", **kwargs)
        self.constraint = constraint


class SchemaError(PersistenceError):
    """Exception raised when database schema issues occur."""

    def __init__(self, message: str, table_name: Optional[str] = None, **kwargs):
        super().__init__(message, operation="schema", **kwargs)
        self.table_name = table_name
