"""SQLite database manager for connection and schema management."""
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Optional

from src.infrastructure.sqlite_provider import SystemSQLiteProvider


class SQLiteManager:
    """Manages SQLite database connections and schema migrations."""

    def __init__(self, db_path: str, sqlite_provider):
        """Initialize SQLite manager.

        Args:
            db_path: Path to the SQLite database file
            sqlite_provider: SQLite操作プロバイダー
        """
        self.db_path = Path(db_path)
        self._sqlite_provider = sqlite_provider or self._get_default_sqlite_provider()
        self._ensure_db_directory()
        self._initialize_database()

    def _get_default_sqlite_provider(self):
        """Get default SQLite provider if none provided."""
        return SystemSQLiteProvider()

    def _ensure_db_directory(self) -> None:
        """Ensure the database directory exists."""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

    def _initialize_database(self) -> None:
        """Initialize database and run migrations."""
        with self.get_connection() as conn:
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

    def _run_migrations(self, conn: 'sqlite3.Connection', current_version: int) -> None:
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
                # Log migration info in debug mode or if explicitly enabled
                if hasattr(self, '_debug_migrations') and self._debug_migrations:
                    # Note: Migration logging for debugging - consider using logger if needed
                    pass

                with migration_file.open("r", encoding="utf-8") as f:
                    migration_sql = f.read()

                # Execute migration
                conn.executescript(migration_sql)

                # Record migration
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
        conn = self._sqlite_provider.connect(str(self.db_path))

        # Enable foreign key constraints
        conn.execute("PRAGMA foreign_keys = ON")
        # Use row factory for dict-like access (if supported by provider)
        if hasattr(conn, 'row_factory'):
            conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()  # Auto-commit successful operations
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def execute_query(self, query: str, params: tuple) -> list[dict[str, Any]]:
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

    def execute_command(self, command: str, params: tuple) -> int:
        """Execute an INSERT/UPDATE/DELETE command.

        Args:
            command: SQL command
            params: Command parameters

        Returns:
            Number of affected rows
        """
        with self.get_connection() as conn:
            cursor = conn.execute(command, params)
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
