"""Tests for SQLiteManager class."""
import pytest
import sqlite3
from unittest.mock import Mock, patch, MagicMock, call
from pathlib import Path
import tempfile
import shutil

from src.application.sqlite_manager import SQLiteManager


class TestSQLiteManager:
    """Tests for SQLiteManager class."""
    
    @pytest.fixture
    def mock_sqlite_provider(self):
        """Create a mock SQLite provider."""
        return Mock()
    
    @pytest.fixture
    def mock_file_provider(self):
        """Create a mock file provider."""
        return Mock()
    
    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for test databases."""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    def test_init_with_none_sqlite_provider_raises_error(self, temp_dir, mock_file_provider):
        """Test initialization with None sqlite provider raises ValueError."""
        db_path = f"{temp_dir}/test.db"
        
        with pytest.raises(ValueError, match="sqlite_provider is required and cannot be None"):
            SQLiteManager(db_path, None, mock_file_provider)
    
    def test_init_with_none_file_provider_raises_error(self, temp_dir, mock_sqlite_provider):
        """Test initialization with None file provider raises ValueError."""
        db_path = f"{temp_dir}/test.db"
        
        with pytest.raises(ValueError, match="file_provider is required and cannot be None"):
            SQLiteManager(db_path, mock_sqlite_provider, None)
    
    def test_init_creates_directory_and_initializes_db(self, mock_sqlite_provider, mock_file_provider, temp_dir):
        """Test initialization creates directory and initializes database."""
        db_path = f"{temp_dir}/subdir/test.db"
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_cursor.fetchone.return_value = [0]  # Current version = 0
        mock_conn.execute.return_value = mock_cursor
        mock_sqlite_provider.connect.return_value = mock_conn
        
        manager = SQLiteManager(db_path, mock_sqlite_provider, mock_file_provider)
        
        # Check that create_directory was called with the parent directory
        mock_file_provider.create_directory.assert_called_with(str(Path(db_path).parent), parents=True, exist_ok=True)
        mock_sqlite_provider.connect.assert_called_with(db_path)
        mock_conn.execute.assert_any_call("PRAGMA foreign_keys = ON")
        
        # Check schema_version table creation
        create_table_call = None
        for call_args in mock_conn.execute.call_args_list:
            if "CREATE TABLE IF NOT EXISTS schema_version" in str(call_args):
                create_table_call = call_args
                break
        assert create_table_call is not None
    
    @patch('pathlib.Path.open')
    @patch('pathlib.Path.glob')
    @patch('pathlib.Path.exists')
    def test_run_migrations(self, mock_exists, mock_glob, mock_open, mock_sqlite_provider, mock_file_provider, temp_dir):
        """Test migration execution."""
        db_path = f"{temp_dir}/test.db"
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_cursor.fetchone.return_value = [0]  # Current version = 0
        mock_conn.execute.return_value = mock_cursor
        mock_sqlite_provider.connect.return_value = mock_conn
        
        # Mock migration files
        mock_exists.return_value = True
        mock_migration_file = Mock()
        mock_migration_file.name = "001_initial_schema.sql"
        
        # Mock the open method on the migration file
        mock_file_handle = MagicMock()
        mock_file_handle.read.return_value = "CREATE TABLE test (id INTEGER);"
        mock_file_handle.__enter__.return_value = mock_file_handle
        mock_file_handle.__exit__.return_value = None
        mock_migration_file.open.return_value = mock_file_handle
        
        mock_glob.return_value = [mock_migration_file]
        
        manager = SQLiteManager(db_path, mock_sqlite_provider, mock_file_provider)
        
        # Verify migration was executed
        mock_conn.executescript.assert_called_once_with("CREATE TABLE test (id INTEGER);")
        
        # Verify version was recorded
        version_insert_call = None
        for call_args in mock_conn.execute.call_args_list:
            if "INSERT OR REPLACE INTO schema_version" in str(call_args):
                version_insert_call = call_args
                break
        assert version_insert_call is not None
    
    def test_get_connection_context_manager(self, mock_sqlite_provider, mock_file_provider, temp_dir):
        """Test get_connection context manager behavior."""
        db_path = f"{temp_dir}/test.db"
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_cursor.fetchone.return_value = [0]  # Current version = 0
        mock_conn.execute.return_value = mock_cursor
        mock_sqlite_provider.connect.return_value = mock_conn
        
        manager = SQLiteManager(db_path, mock_sqlite_provider, mock_file_provider)
        
        # Reset mock to test get_connection behavior specifically
        mock_conn.reset_mock()
        mock_sqlite_provider.connect.reset_mock()
        
        # Test successful operation
        with manager.get_connection() as conn:
            assert conn == mock_conn
            mock_conn.execute.assert_called_with("PRAGMA foreign_keys = ON")
        
        mock_conn.commit.assert_called()
        mock_conn.close.assert_called()
    
    def test_get_connection_rollback_on_error(self, mock_sqlite_provider, mock_file_provider, temp_dir):
        """Test get_connection rolls back on error."""
        db_path = f"{temp_dir}/test.db"
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_cursor.fetchone.return_value = [0]  # Current version = 0
        mock_conn.execute.return_value = mock_cursor
        mock_sqlite_provider.connect.return_value = mock_conn
        
        manager = SQLiteManager(db_path, mock_sqlite_provider, mock_file_provider)
        
        # Reset mock to test get_connection behavior specifically
        mock_conn.reset_mock()
        mock_sqlite_provider.connect.reset_mock()
        
        # Test rollback on error
        with pytest.raises(Exception, match="Test error"):
            with manager.get_connection() as conn:
                raise Exception("Test error")
        
        mock_conn.rollback.assert_called()
        mock_conn.close.assert_called()
    
    def test_execute_query(self, mock_sqlite_provider, mock_file_provider, temp_dir):
        """Test execute_query method."""
        db_path = f"{temp_dir}/test.db"
        mock_conn = Mock()
        
        # Setup for initialization
        init_cursor = Mock()
        init_cursor.fetchone.return_value = [0]  # Current version = 0
        
        # Setup for actual query
        query_cursor = Mock()
        mock_row1 = {"id": 1, "name": "test1"}
        mock_row2 = {"id": 2, "name": "test2"}
        query_cursor.fetchall.return_value = [mock_row1, mock_row2]
        
        # Return different cursors for different queries
        def execute_side_effect(query, *args):
            if "SELECT MAX(version)" in query:
                return init_cursor
            elif "SELECT * FROM test" in query:
                return query_cursor
            else:
                return Mock()
        
        mock_conn.execute.side_effect = execute_side_effect
        mock_sqlite_provider.connect.return_value = mock_conn
        
        manager = SQLiteManager(db_path, mock_sqlite_provider, mock_file_provider)
        
        result = manager.execute_query("SELECT * FROM test WHERE id > ?", (0,))
        
        assert result == [mock_row1, mock_row2]
    
    def test_execute_command(self, mock_sqlite_provider, mock_file_provider, temp_dir):
        """Test execute_command method."""
        db_path = f"{temp_dir}/test.db"
        mock_conn = Mock()
        
        # Setup for initialization
        init_cursor = Mock()
        init_cursor.fetchone.return_value = [0]  # Current version = 0
        
        # Setup for actual command
        command_cursor = Mock()
        command_cursor.rowcount = 1
        
        # Return different cursors for different queries
        def execute_side_effect(query, *args):
            if "SELECT MAX(version)" in query:
                return init_cursor
            elif "UPDATE test" in query:
                return command_cursor
            else:
                return Mock()
        
        mock_conn.execute.side_effect = execute_side_effect
        mock_sqlite_provider.connect.return_value = mock_conn
        
        manager = SQLiteManager(db_path, mock_sqlite_provider, mock_file_provider)
        
        affected = manager.execute_command("UPDATE test SET name = ? WHERE id = ?", ("updated", 1))
        
        assert affected == 1
    
    def test_get_last_insert_id(self, mock_sqlite_provider, mock_file_provider, temp_dir):
        """Test get_last_insert_id method."""
        db_path = f"{temp_dir}/test.db"
        mock_conn = Mock()
        
        # Setup for initialization
        init_cursor = Mock()
        init_cursor.fetchone.return_value = [0]  # Current version = 0
        
        # Setup for last insert id query
        id_cursor = Mock()
        id_cursor.fetchone.return_value = {"id": 42}
        
        # Return different cursors for different queries
        def execute_side_effect(query, *args):
            if "SELECT MAX(version)" in query:
                return init_cursor
            elif "SELECT last_insert_rowid()" in query:
                return id_cursor
            else:
                return Mock()
        
        mock_conn.execute.side_effect = execute_side_effect
        mock_sqlite_provider.connect.return_value = mock_conn
        
        manager = SQLiteManager(db_path, mock_sqlite_provider, mock_file_provider)
        
        last_id = manager.get_last_insert_id("test_table")
        
        assert last_id == 42
    
    def test_get_last_insert_id_returns_none_for_zero(self, mock_sqlite_provider, mock_file_provider, temp_dir):
        """Test get_last_insert_id returns None when id is 0."""
        db_path = f"{temp_dir}/test.db"
        mock_conn = Mock()
        
        # Setup for initialization
        init_cursor = Mock()
        init_cursor.fetchone.return_value = [0]  # Current version = 0
        
        # Setup for last insert id query
        id_cursor = Mock()
        id_cursor.fetchone.return_value = {"id": 0}
        
        # Return different cursors for different queries
        def execute_side_effect(query, *args):
            if "SELECT MAX(version)" in query:
                return init_cursor
            elif "SELECT last_insert_rowid()" in query:
                return id_cursor
            else:
                return Mock()
        
        mock_conn.execute.side_effect = execute_side_effect
        mock_sqlite_provider.connect.return_value = mock_conn
        
        manager = SQLiteManager(db_path, mock_sqlite_provider, mock_file_provider)
        
        last_id = manager.get_last_insert_id("test_table")
        
        assert last_id is None
    
    def test_row_factory_setting(self, mock_sqlite_provider, mock_file_provider, temp_dir):
        """Test row_factory is set if supported by provider."""
        db_path = f"{temp_dir}/test.db"
        mock_conn = Mock()
        mock_conn.row_factory = None  # Simulate row_factory attribute
        
        # Setup for initialization
        init_cursor = Mock()
        init_cursor.fetchone.return_value = [0]  # Current version = 0
        mock_conn.execute.return_value = init_cursor
        
        mock_sqlite_provider.connect.return_value = mock_conn
        
        manager = SQLiteManager(db_path, mock_sqlite_provider, mock_file_provider)
        
        # Reset mock to test get_connection behavior specifically
        mock_conn.row_factory = None  # Reset row_factory
        mock_sqlite_provider.connect.reset_mock()
        
        with manager.get_connection() as conn:
            assert conn.row_factory == sqlite3.Row