"""Fast SQLite manager with in-memory support for tests."""
import threading
from contextlib import contextmanager
from pathlib import Path
from typing import TYPE_CHECKING, Any, Optional

if TYPE_CHECKING:
    import sqlite3


class FastSQLiteManager:
    """Fast SQLite manager with shared in-memory database for tests."""

    _shared_connection: Optional[Any] = None
    _connection_lock = threading.RLock()
    _migration_applied = False

    def __init__(self, db_path: str = ":memory:", skip_migrations: bool = False, sqlite_provider=None):
        """Initialize Fast SQLite manager.

        Args:
            db_path: Path to SQLite database or ":memory:" for in-memory
            skip_migrations: Skip database migrations if True
            sqlite_provider: SQLite操作プロバイダー
        """
        self.db_path = db_path
        self.skip_migrations = skip_migrations
        self._sqlite_provider = sqlite_provider or self._get_default_sqlite_provider()
        self._is_memory_db = db_path == ":memory:"
        self._initialize_setup()

    def _get_default_sqlite_provider(self):
        """Get default SQLite provider if none provided."""
        from src.infrastructure.providers.sqlite_provider import SystemSQLiteProvider
        return SystemSQLiteProvider()

    def _initialize_setup(self):
        """Initialize database setup."""
        if not self._is_memory_db:
            # For file databases, ensure directory exists
            db_path_obj = Path(self.db_path)
            db_path_obj.parent.mkdir(parents=True, exist_ok=True)

        self._initialize_database()

    def _initialize_database(self) -> None:
        """Initialize database and run migrations if needed."""
        if self._is_memory_db:
            self._initialize_shared_memory_db()
        else:
            self._initialize_file_db()

    def _initialize_shared_memory_db(self) -> None:
        """Initialize shared in-memory database."""
        with self._connection_lock:
            if FastSQLiteManager._shared_connection is None:
                FastSQLiteManager._shared_connection = self._sqlite_provider.connect(":memory:", check_same_thread=False)
                self._setup_connection(FastSQLiteManager._shared_connection)

                if not self.skip_migrations:
                    self._run_migrations(FastSQLiteManager._shared_connection)
                    FastSQLiteManager._migration_applied = True
            elif not FastSQLiteManager._migration_applied and not self.skip_migrations:
                self._run_migrations(FastSQLiteManager._shared_connection)
                FastSQLiteManager._migration_applied = True

    def _initialize_file_db(self) -> None:
        """Initialize file-based database."""
        with self.get_connection() as conn:
            if not self.skip_migrations:
                # Create schema_version table if it doesn't exist
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS schema_version (
                        id INTEGER PRIMARY KEY,
                        version INTEGER NOT NULL,
                        applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                conn.commit()

                # Check current schema version
                cursor = conn.execute("SELECT MAX(version) FROM schema_version")
                row = cursor.fetchone()
                current_version = row[0] if row and row[0] is not None else 0

                # Run migrations
                self._run_migrations(conn, current_version)

    def _setup_connection(self, conn: 'sqlite3.Connection') -> None:
        """Setup connection with required pragmas and settings."""
        conn.execute("PRAGMA foreign_keys = ON")
        # Set row_factory if supported
        if hasattr(conn, 'row_factory'):
            import sqlite3
            conn.row_factory = sqlite3.Row

    def _run_migrations(self, conn: 'sqlite3.Connection', current_version: int = 0) -> None:
        """Run database migrations.

        Args:
            conn: Database connection
            current_version: Current schema version
        """
        migrations_dir = Path(__file__).parent / "migrations"

        if not migrations_dir.exists():
            return

        # Find migration files
        migration_files = sorted([
            f for f in migrations_dir.glob("*.sql")
            if f.name.split("_")[0].isdigit()
        ])

        for migration_file in migration_files:
            version = int(migration_file.name.split("_")[0])

            if version > current_version:
                with migration_file.open("r", encoding="utf-8") as f:
                    migration_sql = f.read()

                # Execute migration
                conn.executescript(migration_sql)

                # Record migration (only for file databases)
                if not self._is_memory_db:
                    conn.execute(
                        "INSERT OR REPLACE INTO schema_version (id, version) VALUES (?, ?)",
                        (1, version)
                    )

                conn.commit()

    @contextmanager
    def get_connection(self):
        """Get a database connection with proper cleanup.

        Yields:
            Database connection
        """
        if self._is_memory_db:
            # Use shared connection for in-memory database
            with self._connection_lock:
                if FastSQLiteManager._shared_connection is None:
                    raise RuntimeError("Shared connection not initialized")
                yield FastSQLiteManager._shared_connection
        else:
            # Create new connection for file database
            conn = self._sqlite_provider.connect(self.db_path)
            self._setup_connection(conn)
            try:
                yield conn
                conn.commit()
            except Exception:
                conn.rollback()
                raise
            finally:
                conn.close()

    def execute_query(self, query: str, params: tuple = ()) -> list[dict[str, Any]]:
        """Execute a SELECT query and return results.

        Args:
            query: SQL query
            params: Query parameters

        Returns:
            List of query results as dictionaries
        """
        with self.get_connection() as conn:
            cursor = conn.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]

    def execute_command(self, command: str, params: tuple = ()) -> int:
        """Execute an INSERT/UPDATE/DELETE command.

        Args:
            command: SQL command
            params: Command parameters

        Returns:
            Number of affected rows
        """
        with self.get_connection() as conn:
            cursor = conn.execute(command, params)
            if not self._is_memory_db:
                conn.commit()
            return cursor.rowcount

    def get_last_insert_id(self, table_name: str) -> Optional[int]:
        """Get the last inserted ID for a table.

        Args:
            table_name: Name of the table

        Returns:
            Last inserted ID or None
        """
        with self.get_connection() as conn:
            cursor = conn.execute("SELECT last_insert_rowid() as id")
            result = cursor.fetchone()
            return result["id"] if result and result["id"] > 0 else None

    def cleanup_test_data(self) -> None:
        """Clean up test data from database."""
        # Order matters due to foreign key constraints
        cleanup_order = [
            "container_lifecycle_events",
            "docker_containers",
            "docker_images",
            "operations",
            "sessions"
        ]

        with self.get_connection() as conn:
            for table in cleanup_order:
                try:
                    conn.execute(f"DELETE FROM {table}")
                except Exception:
                    # Table might not exist, continue
                    continue

            # Ensure changes are committed for file databases
            if not self._is_memory_db:
                conn.commit()

    @classmethod
    def reset_shared_connection(cls) -> None:
        """Reset shared connection (for test isolation)."""
        with cls._connection_lock:
            if cls._shared_connection:
                cls._shared_connection.close()
            cls._shared_connection = None
            cls._migration_applied = False
