import pytest
from unittest.mock import Mock, patch, MagicMock
import sqlite3
from datetime import datetime
from pathlib import Path

from src.application.fast_sqlite_manager import FastSQLiteManager, PersistenceError
from src.operations.results.result import ValidationResult


class TestFastSQLiteManager:
    @pytest.fixture
    def mock_sqlite_provider(self):
        provider = Mock()
        # Mock the connection object
        mock_conn = Mock(spec=sqlite3.Connection)
        mock_cursor = Mock()
        mock_conn.cursor.return_value = mock_cursor
        mock_conn.execute.return_value = mock_cursor
        mock_cursor.fetchone.return_value = None
        mock_cursor.fetchall.return_value = []
        provider.connect.return_value = mock_conn
        return provider

    @pytest.fixture
    def mock_file_provider(self):
        return Mock()

    @pytest.fixture
    def manager(self, mock_sqlite_provider, mock_file_provider):
        # Reset class-level state
        FastSQLiteManager._shared_connection = None
        FastSQLiteManager._migration_applied = False
        return FastSQLiteManager(":memory:", skip_migrations=True, sqlite_provider=mock_sqlite_provider, file_provider=mock_file_provider)

    def test_init(self, mock_sqlite_provider, mock_file_provider):
        manager = FastSQLiteManager(":memory:", skip_migrations=True, sqlite_provider=mock_sqlite_provider, file_provider=mock_file_provider)
        assert manager._sqlite_provider == mock_sqlite_provider
        assert manager.db_path == ":memory:"
        assert manager.skip_migrations is True
        assert manager._is_memory_db is True

    def test_init_file_db(self, mock_sqlite_provider, mock_file_provider):
        # Mock connection for validation
        mock_conn = Mock(spec=sqlite3.Connection)
        mock_cursor = Mock()
        mock_conn.execute.return_value = mock_cursor
        
        # Mock for validation query "SELECT 1"
        mock_cursor.fetchone.return_value = (1,)
        
        # Mock for schema version check
        mock_cursor.fetchone.side_effect = [(1,), (0,)]  # First for validation, second for schema version
        
        mock_sqlite_provider.connect.return_value = mock_conn
        
        with patch('pathlib.Path.mkdir'):
            manager = FastSQLiteManager("/tmp/test.db", skip_migrations=False, sqlite_provider=mock_sqlite_provider, file_provider=mock_file_provider)
            assert manager.db_path == "/tmp/test.db"
            assert manager._is_memory_db is False

    def test_get_connection_memory_db(self, manager, mock_sqlite_provider):
        # For memory databases, connection is already set during initialization
        # Get the connection that was set during manager initialization
        with manager.get_connection() as conn:
            assert conn is not None
            assert conn == FastSQLiteManager._shared_connection
        
        # Shared connection should be initialized
        assert FastSQLiteManager._shared_connection is not None

    def test_execute_query(self, manager, mock_sqlite_provider):
        # Create a class that behaves like a SQLite Row
        class MockRow:
            def __init__(self, data):
                self._data = data
            
            def keys(self):
                return list(self._data.keys())
            
            def __iter__(self):
                return iter(self._data.items())
            
            def __getitem__(self, key):
                return self._data[key]
        
        # Get the actual shared connection to mock its execute method
        with manager.get_connection() as conn:
            mock_cursor = Mock()
            mock_row1 = MockRow({"id": 1, "name": "test1"})
            mock_row2 = MockRow({"id": 2, "name": "test2"})
            mock_cursor.fetchall.return_value = [mock_row1, mock_row2]
            conn.execute = Mock(return_value=mock_cursor)
        
        results = manager.execute_query("SELECT * FROM test", ())
        
        assert len(results) == 2
        assert results[0]["id"] == 1
        assert results[0]["name"] == "test1"

    def test_execute_command(self, manager, mock_sqlite_provider):
        # Get the actual shared connection to mock its execute method
        with manager.get_connection() as conn:
            mock_cursor = Mock()
            mock_cursor.rowcount = 5
            conn.execute = Mock(return_value=mock_cursor)
        
        row_count = manager.execute_command("UPDATE test SET active = 1", ())
        
        assert row_count == 5

    def test_execute_command_error(self, manager, mock_sqlite_provider):
        # Since execute_command doesn't have try-except, errors will propagate
        with manager.get_connection() as conn:
            conn.execute = Mock(side_effect=sqlite3.Error("Database error"))
        
        with pytest.raises(sqlite3.Error):
            manager.execute_command("INVALID SQL", ())

    def test_get_last_insert_id(self, manager, mock_sqlite_provider):
        # Get the actual shared connection to mock its execute method
        with manager.get_connection() as conn:
            mock_cursor = Mock()
            # Create a MockRow for the result
            class MockRow:
                def __getitem__(self, key):
                    if key == "id" or key == 0:
                        return 42
                    return None
            
            mock_cursor.fetchone.return_value = MockRow()
            conn.execute = Mock(return_value=mock_cursor)
        
        last_id = manager.get_last_insert_id("test_table")
        
        assert last_id == 42

    def test_cleanup_test_data(self, manager, mock_sqlite_provider):
        # Mock the _table_exists and _execute_table_cleanup methods
        manager._table_exists = Mock(side_effect=lambda conn, table: table in ["container_lifecycle_events", "docker_containers"])
        manager._execute_table_cleanup = Mock(return_value=Mock(is_success=lambda: True, get_message=lambda: ""))
        
        manager.cleanup_test_data()
        
        # Should check existence and cleanup for expected tables
        assert manager._table_exists.call_count >= 2
        assert manager._execute_table_cleanup.call_count >= 2

    def test_reset_shared_connection(self):
        # Set up shared connection
        FastSQLiteManager._shared_connection = Mock()
        FastSQLiteManager._migration_applied = True
        
        FastSQLiteManager.reset_shared_connection()
        
        assert FastSQLiteManager._shared_connection is None
        assert FastSQLiteManager._migration_applied is False

    def test_run_migrations(self, mock_sqlite_provider, mock_file_provider):
        # Mock connection for file database
        mock_conn = Mock(spec=sqlite3.Connection)
        mock_cursor = Mock()
        mock_conn.execute.return_value = mock_cursor
        
        # Mock for validation query "SELECT 1"
        validation_cursor = Mock()
        validation_cursor.fetchone.return_value = (1,)
        
        # Set up execute to return different cursors based on query
        def execute_side_effect(query, params=()):
            if "SELECT 1" in query:
                return validation_cursor
            elif "SELECT MAX(version)" in query:
                cursor = Mock()
                cursor.fetchone.return_value = (0,)
                return cursor
            return mock_cursor
        
        mock_conn.execute.side_effect = execute_side_effect
        mock_sqlite_provider.connect.return_value = mock_conn
        
        # Mock migration files
        with patch('pathlib.Path.exists') as mock_exists:
            with patch('pathlib.Path.glob') as mock_glob:
                mock_exists.return_value = True
                mock_migration = Mock()
                mock_migration.name = "001_initial.sql"
                # Create a proper context manager mock for file open
                mock_file = MagicMock()
                mock_file.read.return_value = "CREATE TABLE test (id INT);"
                mock_migration.open.return_value.__enter__ = Mock(return_value=mock_file)
                mock_migration.open.return_value.__exit__ = Mock(return_value=None)
                mock_glob.return_value = [mock_migration]
                
                with patch('pathlib.Path.mkdir'):
                    manager = FastSQLiteManager("/tmp/test.db", skip_migrations=False, sqlite_provider=mock_sqlite_provider, file_provider=mock_file_provider)
                
                # Should execute migration
                mock_conn.executescript.assert_called()

    def test_table_exists(self, manager, mock_sqlite_provider):
        # Create a mock connection
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_conn.execute.return_value = mock_cursor
        mock_cursor.fetchone.return_value = ("test_table",)
        
        # Access private method for testing
        result = manager._table_exists(mock_conn, "test_table")
        
        assert result is True
        # Check that the correct query was executed
        mock_conn.execute.assert_called_once()
        query = mock_conn.execute.call_args[0][0]
        assert "sqlite_master" in query
        assert mock_conn.execute.call_args[0][1] == ("test_table",)

    def test_connection_validation(self, manager):
        mock_conn = Mock()
        mock_conn.execute.return_value.fetchone.return_value = (1,)
        
        result = manager._validate_connection(mock_conn)
        
        assert isinstance(result, ValidationResult)
        assert result.is_valid