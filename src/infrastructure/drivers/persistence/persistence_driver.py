"""Persistence driver implementation following infrastructure patterns."""
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from contextlib import contextmanager

from src.infrastructure.drivers.base.base_driver import BaseDriver
from src.domain.interfaces.persistence_interface import PersistenceInterface


class PersistenceDriver(BaseDriver, PersistenceInterface):
    """Abstract base class for persistence drivers."""

    @abstractmethod
    def get_connection(self) -> Any:
        """Get a database connection."""
        pass

    @abstractmethod
    def execute_query(self, query: str, params: tuple = ()) -> List[Dict[str, Any]]:
        """Execute a SELECT query and return results."""
        pass

    @abstractmethod
    def execute_command(self, command: str, params: tuple = ()) -> int:
        """Execute an INSERT/UPDATE/DELETE command."""
        pass

    @abstractmethod
    def begin_transaction(self) -> Any:
        """Begin a database transaction."""
        pass

    @abstractmethod
    def get_repository(self, repository_class: type) -> Any:
        """Get a repository instance."""
        pass

    # BaseDriver abstract methods
    def execute(self, request: Any) -> Any:
        """Execute a persistence request.
        
        Args:
            request: The persistence request to execute
            
        Returns:
            The execution result
        """
        if hasattr(request, 'query'):
            return self.execute_query(request.query, getattr(request, 'params', ()))
        elif hasattr(request, 'command'):
            return self.execute_command(request.command, getattr(request, 'params', ()))
        else:
            raise ValueError(f"Unsupported request type: {type(request)}")

    def validate(self, request: Any) -> bool:
        """Validate if the driver can handle the persistence request.
        
        Args:
            request: The request object to validate
            
        Returns:
            True if the driver can handle the request, False otherwise
        """
        return hasattr(request, 'query') or hasattr(request, 'command')


class SQLitePersistenceDriver(PersistenceDriver):
    """SQLite implementation of persistence driver."""

    def __init__(self, db_path: str = "cph_history.db"):
        """Initialize SQLite persistence driver.
        
        Args:
            db_path: Path to the SQLite database file
        """
        self.db_path = db_path
        self._repositories = {}
        self._initialize_database()

    def _initialize_database(self) -> None:
        """Initialize database and run migrations."""
        from src.infrastructure.persistence.sqlite.sqlite_manager import SQLiteManager
        self._sqlite_manager = SQLiteManager(self.db_path)

    def get_connection(self) -> Any:
        """Get a database connection."""
        return self._sqlite_manager.get_connection()

    def execute_query(self, query: str, params: tuple = ()) -> List[Dict[str, Any]]:
        """Execute a SELECT query and return results."""
        return self._sqlite_manager.execute_query(query, params)

    def execute_command(self, command: str, params: tuple = ()) -> int:
        """Execute an INSERT/UPDATE/DELETE command."""
        return self._sqlite_manager.execute_command(command, params)

    @contextmanager
    def begin_transaction(self) -> Any:
        """Begin a database transaction."""
        with self.get_connection() as conn:
            try:
                yield conn
                # Note: commit is handled by SQLiteManager's context manager
            except Exception:
                conn.rollback()
                raise

    def get_repository(self, repository_class: type) -> Any:
        """Get a repository instance.
        
        Args:
            repository_class: Repository class to instantiate
            
        Returns:
            Repository instance
        """
        repo_name = repository_class.__name__
        
        if repo_name not in self._repositories:
            self._repositories[repo_name] = repository_class(self._sqlite_manager)
        
        return self._repositories[repo_name]

    def initialize(self) -> None:
        """Initialize the persistence driver."""
        # Database initialization is handled in constructor
        pass

    def cleanup(self) -> None:
        """Cleanup persistence driver resources."""
        self._repositories.clear()