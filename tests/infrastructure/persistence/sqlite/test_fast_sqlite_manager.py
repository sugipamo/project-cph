"""Tests for FastSQLiteManager"""

import tempfile
import threading
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest

from src.infrastructure.persistence.sqlite.fast_sqlite_manager import FastSQLiteManager


class TestFastSQLiteManager:
    """Tests for FastSQLiteManager class"""

    def setup_method(self):
        """Setup for each test method"""
        # Reset class variables
        FastSQLiteManager._shared_connection = None
        FastSQLiteManager._migration_applied = False

    def teardown_method(self):
        """Cleanup after each test method"""
        # Reset class variables
        FastSQLiteManager.reset_shared_connection()

    def test_init_memory_database_default(self):
        """Test initialization with default in-memory database"""
        manager = FastSQLiteManager()

        assert manager.db_path == ":memory:"
        assert manager.skip_migrations is False
        assert manager._is_memory_db is True

    def test_init_file_database(self):
        """Test initialization with file database"""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
            db_path = tmp.name

        try:
            manager = FastSQLiteManager(db_path=db_path)

            assert manager.db_path == db_path
            assert manager._is_memory_db is False
        finally:
            Path(db_path).unlink(missing_ok=True)

    def test_init_skip_migrations(self):
        """Test initialization with skip_migrations=True"""
        manager = FastSQLiteManager(skip_migrations=True)

        assert manager.skip_migrations is True

    @patch('src.infrastructure.providers.sqlite_provider.SystemSQLiteProvider')
    def test_init_custom_sqlite_provider(self, mock_provider_class):
        """Test initialization with custom SQLite provider"""
        mock_provider = Mock()
        manager = FastSQLiteManager(sqlite_provider=mock_provider)

        assert manager._sqlite_provider == mock_provider
        mock_provider_class.assert_not_called()

    @patch('src.infrastructure.providers.sqlite_provider.SystemSQLiteProvider')
    def test_get_default_sqlite_provider(self, mock_provider_class):
        """Test _get_default_sqlite_provider method"""
        mock_provider = Mock()
        mock_provider_class.return_value = mock_provider

        manager = FastSQLiteManager()

        assert manager._sqlite_provider == mock_provider
        mock_provider_class.assert_called_once()

    @patch('src.infrastructure.persistence.sqlite.fast_sqlite_manager.Path')
    def test_initialize_setup_file_database(self, mock_path):
        """Test _initialize_setup for file database"""
        mock_path_obj = Mock()
        mock_path.return_value = mock_path_obj

        with patch.object(FastSQLiteManager, '_initialize_database'):
            FastSQLiteManager(db_path="/test/db.sqlite")

        mock_path.assert_called_with("/test/db.sqlite")
        mock_path_obj.parent.mkdir.assert_called_once_with(parents=True, exist_ok=True)

    def test_initialize_shared_memory_db_first_time(self):
        """Test _initialize_shared_memory_db when called first time"""
        mock_provider = Mock()
        mock_connection = Mock()
        mock_provider.connect.return_value = mock_connection

        FastSQLiteManager(sqlite_provider=mock_provider)

        # The connection should be set up during initialization
        assert FastSQLiteManager._shared_connection == mock_connection
        mock_provider.connect.assert_called_with(":memory:", check_same_thread=False)

    def test_initialize_shared_memory_db_subsequent_calls(self):
        """Test _initialize_shared_memory_db on subsequent calls"""
        mock_provider = Mock()
        mock_connection = Mock()
        mock_provider.connect.return_value = mock_connection

        # First manager
        FastSQLiteManager(sqlite_provider=mock_provider)
        first_connection = FastSQLiteManager._shared_connection

        # Second manager should reuse connection
        FastSQLiteManager(sqlite_provider=mock_provider)

        assert FastSQLiteManager._shared_connection == first_connection
        # connect should only be called once
        mock_provider.connect.assert_called_once()

    def test_setup_connection(self):
        """Test _setup_connection method"""
        mock_connection = Mock()
        mock_connection.row_factory = None  # Simulate sqlite3.Connection

        manager = FastSQLiteManager(skip_migrations=True)
        manager._setup_connection(mock_connection)

        mock_connection.execute.assert_called_with("PRAGMA foreign_keys = ON")

    def test_get_connection_memory_database(self):
        """Test get_connection for in-memory database"""
        mock_provider = Mock()
        mock_connection = Mock()
        mock_provider.connect.return_value = mock_connection

        manager = FastSQLiteManager(sqlite_provider=mock_provider, skip_migrations=True)

        with manager.get_connection() as conn:
            assert conn == mock_connection

    def test_get_connection_file_database(self):
        """Test get_connection for file database"""
        mock_provider = Mock()
        mock_connection = Mock()
        mock_provider.connect.return_value = mock_connection

        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
            db_path = tmp.name

        try:
            with patch.object(FastSQLiteManager, '_initialize_database'):
                manager = FastSQLiteManager(db_path=db_path, sqlite_provider=mock_provider, skip_migrations=True)

            with manager.get_connection() as conn:
                assert conn == mock_connection

            mock_connection.commit.assert_called_once()
            mock_connection.close.assert_called_once()
        finally:
            Path(db_path).unlink(missing_ok=True)

    def test_get_connection_file_database_with_exception(self):
        """Test get_connection for file database when exception occurs"""
        mock_provider = Mock()
        mock_connection = Mock()
        mock_provider.connect.return_value = mock_connection

        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
            db_path = tmp.name

        try:
            with patch.object(FastSQLiteManager, '_initialize_database'):
                manager = FastSQLiteManager(db_path=db_path, sqlite_provider=mock_provider, skip_migrations=True)

            with pytest.raises(RuntimeError), manager.get_connection():
                raise RuntimeError("Test exception")

            mock_connection.rollback.assert_called_once()
            mock_connection.close.assert_called_once()
        finally:
            Path(db_path).unlink(missing_ok=True)

    def test_execute_query(self):
        """Test execute_query method"""
        mock_provider = Mock()
        mock_connection = Mock()
        mock_cursor = Mock()
        mock_row1 = {"id": 1, "name": "test1"}
        mock_row2 = {"id": 2, "name": "test2"}

        mock_connection.execute.return_value = mock_cursor
        mock_cursor.fetchall.return_value = [mock_row1, mock_row2]
        mock_provider.connect.return_value = mock_connection

        manager = FastSQLiteManager(sqlite_provider=mock_provider, skip_migrations=True)

        result = manager.execute_query("SELECT * FROM test", ("param1",))

        assert result == [mock_row1, mock_row2]
        mock_connection.execute.assert_called_with("SELECT * FROM test", ("param1",))

    def test_execute_command_memory_database(self):
        """Test execute_command for in-memory database"""
        mock_provider = Mock()
        mock_connection = Mock()
        mock_cursor = Mock()
        mock_cursor.rowcount = 5

        mock_connection.execute.return_value = mock_cursor
        mock_provider.connect.return_value = mock_connection

        manager = FastSQLiteManager(sqlite_provider=mock_provider, skip_migrations=True)

        result = manager.execute_command("INSERT INTO test VALUES (?)", ("value1",))

        assert result == 5
        mock_connection.execute.assert_called_with("INSERT INTO test VALUES (?)", ("value1",))
        # commit should not be called for memory database
        mock_connection.commit.assert_not_called()

    def test_execute_command_file_database(self):
        """Test execute_command for file database"""
        mock_provider = Mock()
        mock_connection = Mock()
        mock_cursor = Mock()
        mock_cursor.rowcount = 3

        mock_connection.execute.return_value = mock_cursor
        mock_provider.connect.return_value = mock_connection

        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
            db_path = tmp.name

        try:
            with patch.object(FastSQLiteManager, '_initialize_database'):
                manager = FastSQLiteManager(db_path=db_path, sqlite_provider=mock_provider, skip_migrations=True)

            # Override the connection for testing
            with patch.object(manager, 'get_connection') as mock_get_conn:
                mock_get_conn.return_value.__enter__.return_value = mock_connection
                mock_get_conn.return_value.__exit__.return_value = None

                result = manager.execute_command("UPDATE test SET name = ?", ("new_name",))

            assert result == 3
        finally:
            Path(db_path).unlink(missing_ok=True)

    def test_get_last_insert_id(self):
        """Test get_last_insert_id method"""
        mock_provider = Mock()
        mock_connection = Mock()
        mock_cursor = Mock()
        mock_cursor.fetchone.return_value = {"id": 42}

        mock_connection.execute.return_value = mock_cursor
        mock_provider.connect.return_value = mock_connection

        manager = FastSQLiteManager(sqlite_provider=mock_provider, skip_migrations=True)

        result = manager.get_last_insert_id("test_table")

        assert result == 42
        mock_connection.execute.assert_called_with("SELECT last_insert_rowid() as id")

    def test_get_last_insert_id_no_result(self):
        """Test get_last_insert_id when no result"""
        mock_provider = Mock()
        mock_connection = Mock()
        mock_cursor = Mock()
        mock_cursor.fetchone.return_value = None

        mock_connection.execute.return_value = mock_cursor
        mock_provider.connect.return_value = mock_connection

        manager = FastSQLiteManager(sqlite_provider=mock_provider, skip_migrations=True)

        result = manager.get_last_insert_id("test_table")

        assert result is None

    def test_get_last_insert_id_zero_result(self):
        """Test get_last_insert_id when result is zero"""
        mock_provider = Mock()
        mock_connection = Mock()
        mock_cursor = Mock()
        mock_cursor.fetchone.return_value = {"id": 0}

        mock_connection.execute.return_value = mock_cursor
        mock_provider.connect.return_value = mock_connection

        manager = FastSQLiteManager(sqlite_provider=mock_provider, skip_migrations=True)

        result = manager.get_last_insert_id("test_table")

        assert result is None

    def test_cleanup_test_data(self):
        """Test cleanup_test_data method"""
        mock_provider = Mock()
        mock_connection = Mock()
        mock_provider.connect.return_value = mock_connection

        manager = FastSQLiteManager(sqlite_provider=mock_provider, skip_migrations=True)

        manager.cleanup_test_data()

        # Check that DELETE statements were called for each table in order
        # First call is PRAGMA foreign_keys = ON from _setup_connection
        expected_calls = [
            ("PRAGMA foreign_keys = ON",),
            ("DELETE FROM container_lifecycle_events",),
            ("DELETE FROM docker_containers",),
            ("DELETE FROM docker_images",),
            ("DELETE FROM operations",),
            ("DELETE FROM sessions",)
        ]

        actual_calls = [call[0] for call in mock_connection.execute.call_args_list]
        assert actual_calls == expected_calls

    def test_cleanup_test_data_with_exception(self):
        """Test cleanup_test_data method when table doesn't exist"""
        mock_provider = Mock()
        mock_connection = Mock()
        # First exception for PRAGMA, then 5 for the DELETE statements
        mock_connection.execute.side_effect = [None, Exception("Table not found"), None, None, None, None]
        mock_provider.connect.return_value = mock_connection

        manager = FastSQLiteManager(sqlite_provider=mock_provider, skip_migrations=True)

        # Should not raise exception
        manager.cleanup_test_data()

        assert mock_connection.execute.call_count == 6  # PRAGMA + 5 DELETE statements

    def test_reset_shared_connection(self):
        """Test reset_shared_connection class method"""
        mock_provider = Mock()
        mock_connection = Mock()
        mock_provider.connect.return_value = mock_connection

        # Set up shared connection
        FastSQLiteManager(sqlite_provider=mock_provider, skip_migrations=True)
        assert FastSQLiteManager._shared_connection is not None

        # Reset connection
        FastSQLiteManager.reset_shared_connection()

        assert FastSQLiteManager._shared_connection is None
        assert FastSQLiteManager._migration_applied is False
        mock_connection.close.assert_called_once()

    def test_reset_shared_connection_when_none(self):
        """Test reset_shared_connection when no shared connection exists"""
        FastSQLiteManager._shared_connection = None

        # Should not raise exception
        FastSQLiteManager.reset_shared_connection()

        assert FastSQLiteManager._shared_connection is None

    def test_thread_safety(self):
        """Test thread safety of shared connection"""
        mock_provider = Mock()
        mock_connection = Mock()
        mock_provider.connect.return_value = mock_connection

        results = []

        def create_manager():
            manager = FastSQLiteManager(sqlite_provider=mock_provider, skip_migrations=True)
            results.append(manager)

        # Create managers from multiple threads
        threads = []
        for _ in range(5):
            thread = threading.Thread(target=create_manager)
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

        # All managers should use the same shared connection
        assert len(results) == 5
        assert all(FastSQLiteManager._shared_connection == mock_connection for _ in results)
        # connect should only be called once due to thread safety
        mock_provider.connect.assert_called_once()
