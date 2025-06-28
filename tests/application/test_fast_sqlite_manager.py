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
    def manager(self, mock_sqlite_provider):
        # Reset class-level state
        FastSQLiteManager._shared_connection = None
        FastSQLiteManager._migration_applied = False
        return FastSQLiteManager(":memory:", skip_migrations=True, sqlite_provider=mock_sqlite_provider)

    def test_init(self, mock_sqlite_provider):
        manager = FastSQLiteManager(":memory:", skip_migrations=True, sqlite_provider=mock_sqlite_provider)
        assert manager._sqlite_provider == mock_sqlite_provider
        assert manager.db_path == ":memory:"
        assert manager.skip_migrations is True
        assert manager._is_memory_db is True

    def test_init_file_db(self, mock_sqlite_provider):
        with patch('pathlib.Path.mkdir'):
            manager = FastSQLiteManager("/tmp/test.db", skip_migrations=False, sqlite_provider=mock_sqlite_provider)
            assert manager.db_path == "/tmp/test.db"
            assert manager._is_memory_db is False

    def test_get_connection_memory_db(self, manager, mock_sqlite_provider):
        mock_conn = Mock()
        mock_sqlite_provider.connect.return_value = mock_conn
        
        with manager.get_connection() as conn:
            assert conn == mock_conn
        
        # Should initialize shared connection
        assert FastSQLiteManager._shared_connection == mock_conn

    def test_execute_query(self, manager, mock_sqlite_provider):
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.fetchall.return_value = [
            {"id": 1, "name": "test1"},
            {"id": 2, "name": "test2"}
        ]
        mock_sqlite_provider.connect.return_value = mock_conn
        
        results = manager.execute_query("SELECT * FROM test", ())
        
        assert len(results) == 2
        assert results[0]["id"] == 1
        assert results[0]["name"] == "test1"

    def test_execute_command(self, manager, mock_sqlite_provider):
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.rowcount = 5
        mock_sqlite_provider.connect.return_value = mock_conn
        
        row_count = manager.execute_command("UPDATE test SET active = 1", ())
        
        assert row_count == 5
        mock_conn.commit.assert_called_once()

    def test_execute_command_error(self, manager, mock_sqlite_provider):
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.execute.side_effect = sqlite3.Error("Database error")
        mock_sqlite_provider.connect.return_value = mock_conn
        
        with pytest.raises(PersistenceError):
            manager.execute_command("INVALID SQL", ())
        
        mock_conn.rollback.assert_called_once()

    def test_get_last_insert_id(self, manager, mock_sqlite_provider):
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.fetchone.return_value = (42,)
        mock_sqlite_provider.connect.return_value = mock_conn
        
        last_id = manager.get_last_insert_id("test_table")
        
        assert last_id == 42
        # Should query sqlite_sequence table
        assert "sqlite_sequence" in mock_cursor.execute.call_args[0][0]

    def test_cleanup_test_data(self, manager, mock_sqlite_provider):
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.fetchall.return_value = [("table1",), ("table2",)]
        mock_sqlite_provider.connect.return_value = mock_conn
        
        manager.cleanup_test_data()
        
        # Should query for tables and delete from them
        assert mock_cursor.execute.call_count >= 1
        mock_conn.commit.assert_called()

    def test_reset_shared_connection(self):
        # Set up shared connection
        FastSQLiteManager._shared_connection = Mock()
        FastSQLiteManager._migration_applied = True
        
        FastSQLiteManager.reset_shared_connection()
        
        assert FastSQLiteManager._shared_connection is None
        assert FastSQLiteManager._migration_applied is False

    def test_run_migrations(self, mock_sqlite_provider):
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_conn.execute.return_value = mock_cursor
        mock_cursor.fetchone.return_value = (0,)  # Current version
        mock_sqlite_provider.connect.return_value = mock_conn
        
        # Mock migration files
        with patch('pathlib.Path.exists') as mock_exists:
            with patch('pathlib.Path.glob') as mock_glob:
                mock_exists.return_value = True
                mock_migration = Mock()
                mock_migration.name = "001_initial.sql"
                mock_migration.open.return_value.__enter__.return_value.read.return_value = "CREATE TABLE test (id INT);"
                mock_glob.return_value = [mock_migration]
                
                manager = FastSQLiteManager("/tmp/test.db", skip_migrations=False, sqlite_provider=mock_sqlite_provider)
                
                # Should execute migration
                mock_conn.executescript.assert_called()

    def test_table_exists(self, manager, mock_sqlite_provider):
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_conn.execute.return_value = mock_cursor
        mock_cursor.fetchone.return_value = (1,)
        mock_sqlite_provider.connect.return_value = mock_conn
        
        # Access private method for testing
        result = manager._table_exists(mock_conn, "test_table")
        
        assert result is True
        assert "sqlite_master" in mock_cursor.execute.call_args[0][0]

    def test_connection_validation(self, manager):
        mock_conn = Mock()
        mock_conn.execute.return_value.fetchone.return_value = (1,)
        
        result = manager._validate_connection(mock_conn)
        
        assert isinstance(result, ValidationResult)
        assert result.is_valid