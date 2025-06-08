"""Tests for SQLiteManager - core database connection and migration handling."""
import os
import tempfile
from pathlib import Path

import pytest

from src.infrastructure.persistence.sqlite.sqlite_manager import SQLiteManager


class TestSQLiteManager:
    """Test SQLite manager core functionality."""

    @pytest.fixture
    def temp_db_path(self):
        """Create temporary database file."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            temp_path = f.name
        yield temp_path
        # Clean up
        if os.path.exists(temp_path):
            os.unlink(temp_path)

    @pytest.fixture
    def sqlite_manager(self, temp_db_path):
        """Create SQLiteManager with temporary database."""
        return SQLiteManager(temp_db_path)

    def test_initialization_with_default_path(self):
        """Test SQLiteManager initializes with default database path."""
        manager = SQLiteManager()
        expected_path = Path("cph_history.db")
        assert manager.db_path == expected_path

    def test_initialization_with_custom_path(self, temp_db_path):
        """Test SQLiteManager initializes with custom database path."""
        manager = SQLiteManager(temp_db_path)
        assert manager.db_path == Path(temp_db_path)

    def test_database_creation(self, sqlite_manager):
        """Test database file is created during initialization."""
        db_path = sqlite_manager.db_path
        # Database should be created during SQLiteManager initialization (due to migrations)
        assert os.path.exists(db_path), "Database file should be created during initialization"

        # Should be able to connect and use the database
        with sqlite_manager.get_connection() as conn:
            result = conn.execute("SELECT 1").fetchone()
            assert result[0] == 1

    def test_connection_context_manager(self, sqlite_manager):
        """Test connection context manager properly opens and closes connections."""
        with sqlite_manager.get_connection() as conn:
            # Should be able to execute queries
            result = conn.execute("SELECT 1").fetchone()
            assert result[0] == 1

    def test_foreign_keys_enabled(self, sqlite_manager):
        """Test foreign key constraints are enabled."""
        with sqlite_manager.get_connection() as conn:
            result = conn.execute("PRAGMA foreign_keys").fetchone()
            assert result[0] == 1, "Foreign keys should be enabled"

    def test_row_factory_configured(self, sqlite_manager):
        """Test row factory is configured for dict-like access."""
        with sqlite_manager.get_connection() as conn:
            conn.execute("CREATE TABLE test_table (id INTEGER, name TEXT)")
            conn.execute("INSERT INTO test_table (id, name) VALUES (1, 'test')")

            row = conn.execute("SELECT * FROM test_table").fetchone()
            assert row["id"] == 1
            assert row["name"] == "test"

    def test_transaction_commit_on_success(self, sqlite_manager):
        """Test transactions are committed on successful context exit."""
        with sqlite_manager.get_connection() as conn:
            conn.execute("CREATE TABLE test_table (id INTEGER)")
            conn.execute("INSERT INTO test_table (id) VALUES (1)")

        # Verify data persisted
        with sqlite_manager.get_connection() as conn:
            result = conn.execute("SELECT COUNT(*) FROM test_table").fetchone()
            assert result[0] == 1

    def test_transaction_rollback_on_exception(self, sqlite_manager):
        """Test transactions are rolled back on exception."""
        # First, create table and insert initial data
        with sqlite_manager.get_connection() as conn:
            conn.execute("CREATE TABLE test_table (id INTEGER UNIQUE)")
            conn.execute("INSERT INTO test_table (id) VALUES (1)")

        # Try to insert duplicate (should fail and rollback)
        import sqlite3
        with pytest.raises(sqlite3.IntegrityError), sqlite_manager.get_connection() as conn:
            conn.execute("INSERT INTO test_table (id) VALUES (2)")  # This should succeed
            conn.execute("INSERT INTO test_table (id) VALUES (1)")  # This should fail (duplicate)

        # Verify rollback occurred - only original data should exist
        with sqlite_manager.get_connection() as conn:
            result = conn.execute("SELECT COUNT(*) FROM test_table").fetchone()
            assert result[0] == 1  # Only original row should exist

    def test_migration_execution(self, sqlite_manager):
        """Test migration system works correctly."""
        # Test should pass if no migrations fail
        # Migrations should be applied automatically when SQLiteManager is used
        with sqlite_manager.get_connection() as conn:
            # Check that schema_version table exists (created by migrations)
            tables = conn.execute("""
                SELECT name FROM sqlite_master
                WHERE type='table' AND name='schema_version'
            """).fetchall()
            assert len(tables) == 1, "schema_version table should exist after migration"

    def test_multiple_connections_same_manager(self, sqlite_manager):
        """Test multiple sequential connections work correctly."""
        # First connection
        with sqlite_manager.get_connection() as conn:
            conn.execute("CREATE TABLE test_table (id INTEGER)")
            conn.execute("INSERT INTO test_table (id) VALUES (1)")

        # Second connection should see the data
        with sqlite_manager.get_connection() as conn:
            result = conn.execute("SELECT COUNT(*) FROM test_table").fetchone()
            assert result[0] == 1

        # Third connection should also work
        with sqlite_manager.get_connection() as conn:
            conn.execute("INSERT INTO test_table (id) VALUES (2)")
            result = conn.execute("SELECT COUNT(*) FROM test_table").fetchone()
            assert result[0] == 2

    def test_connection_isolation(self, temp_db_path):
        """Test different SQLiteManager instances are properly isolated."""
        manager1 = SQLiteManager(temp_db_path)
        manager2 = SQLiteManager(temp_db_path)

        # Both should connect to same database
        with manager1.get_connection() as conn:
            conn.execute("CREATE TABLE test_table (id INTEGER)")
            conn.execute("INSERT INTO test_table (id) VALUES (1)")

        with manager2.get_connection() as conn:
            result = conn.execute("SELECT COUNT(*) FROM test_table").fetchone()
            assert result[0] == 1

    def test_large_transaction(self, sqlite_manager):
        """Test handling of larger transactions."""
        with sqlite_manager.get_connection() as conn:
            conn.execute("CREATE TABLE test_table (id INTEGER, data TEXT)")

            # Insert multiple records in single transaction
            for i in range(100):
                conn.execute("INSERT INTO test_table (id, data) VALUES (?, ?)",
                           (i, f"data_{i}"))

        # Verify all data persisted
        with sqlite_manager.get_connection() as conn:
            result = conn.execute("SELECT COUNT(*) FROM test_table").fetchone()
            assert result[0] == 100
