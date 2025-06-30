"""Persistence driver implementation following infrastructure patterns."""
import json
from abc import abstractmethod
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Dict, List

from old_src.infrastructure.drivers.base.base_driver import ExecutionDriverInterface
from old_src.operations.interfaces.persistence_interface import PersistenceInterface


from old_src.infrastructure.persistence.sqlite.sqlite_manager import SQLiteManager
class PersistenceDriver(ExecutionDriverInterface, PersistenceInterface):
    """Abstract base class for persistence drivers."""

    def __init__(self):
        """Initialize PersistenceDriver with infrastructure defaults."""
        # 互換性維持: 設定システムでgetattr()デフォルト値を管理
        self._infrastructure_defaults = self._load_infrastructure_defaults()

    def _load_infrastructure_defaults(self) -> dict[str, Any]:
        """Load infrastructure defaults from config file."""
        try:
            config_path = Path(__file__).parents[4] / "config" / "system" / "infrastructure_defaults.json"
            with open(config_path, encoding='utf-8') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            # フォールバック: デフォルト値をハードコード
            return {
                "infrastructure_defaults": {
                    "persistence": {"params": []}
                }
            }

    def _get_default_value(self, path: list[str], default_type: type) -> Any:
        """Get default value from infrastructure defaults."""
        current = self._infrastructure_defaults
        for key in path:
            current = current[key]
        if isinstance(current, default_type):
            return current
        # 型が不一致の場合のフォールバック
        if default_type is tuple:
            return ()
        return []

    @abstractmethod
    def get_connection(self) -> Any:
        """Get a database connection."""
        pass

    @abstractmethod
    def execute_query(self, query: str, params: tuple = ()) -> List[Dict[str, Any]]:
        """Execute a SELECT query and return results."""
        pass

    @abstractmethod
    def execute_persistence_command(self, command: str, params: tuple = ()) -> int:
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

    # ExecutionDriverInterface abstract methods
    def execute_command(self, request: Any) -> Any:
        """Execute a persistence request.

        Args:
            request: The persistence request to execute

        Returns:
            The execution result
        """
        if hasattr(request, 'query'):
            # 互換性維持: hasattr()によるgetattr()デフォルト値の代替
            return self.execute_query(request.query, request.params if hasattr(request, 'params') else self._get_default_value(['infrastructure_defaults', 'persistence', 'params'], tuple))
        if hasattr(request, 'command'):
            # 互換性維持: hasattr()によるgetattr()デフォルト値の代替
            return self.execute_persistence_command(request.command, request.params if hasattr(request, 'params') else self._get_default_value(['infrastructure_defaults', 'persistence', 'params'], tuple))
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
        self._sqlite_manager = SQLiteManager(self.db_path)

    def get_connection(self) -> Any:
        """Get a database connection."""
        return self._sqlite_manager.get_connection()

    def execute_query(self, query: str, params: tuple = ()) -> List[Dict[str, Any]]:
        """Execute a SELECT query and return results."""
        return self._sqlite_manager.execute_query(query, params)

    def execute_persistence_command(self, command: str, params: tuple = ()) -> int:
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
