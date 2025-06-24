"""Tests for persistence driver implementation."""
from contextlib import contextmanager
from unittest.mock import MagicMock, Mock, patch

import pytest

from src.infrastructure.drivers.persistence.persistence_driver import PersistenceDriver, SQLitePersistenceDriver


class MockPersistenceDriver(PersistenceDriver):
    """Mock implementation of PersistenceDriver for testing."""

    def __init__(self):
        self.connection = Mock()
        self.query_results = []
        self.command_result = 0

    def get_connection(self):
        return self.connection

    def execute_query(self, query: str, params: tuple = ()):
        return self.query_results

    def execute_persistence_command(self, command: str, params: tuple = ()):
        return self.command_result

    def begin_transaction(self):
        return self.connection

    def get_repository(self, repository_class: type):
        return Mock(spec=repository_class)

    def initialize(self):
        pass

    def cleanup(self):
        pass


class TestPersistenceDriver:
    """Test PersistenceDriver abstract base class."""

    def test_execute_with_query_request(self):
        driver = MockPersistenceDriver()
        driver.query_results = [{"id": 1, "name": "test"}]

        # Create a mock request with query attribute
        request = Mock()
        request.query = "SELECT * FROM test"
        request.params = (1,)

        result = driver.execute_command(request)
        assert result == [{"id": 1, "name": "test"}]

    def test_execute_with_command_request(self):
        driver = MockPersistenceDriver()
        driver.command_result = 5

        # Create a mock request with command attribute
        request = type('Request', (), {'command': "INSERT INTO test VALUES (?)", 'params': ("value",)})()

        result = driver.execute_command(request)
        assert result == 5


    def test_validate_with_query_request(self):
        driver = MockPersistenceDriver()

        request = Mock()
        request.query = "SELECT * FROM test"

        assert driver.validate(request) is True

    def test_validate_with_command_request(self):
        driver = MockPersistenceDriver()

        request = Mock()
        request.command = "INSERT INTO test VALUES (?)"

        assert driver.validate(request) is True

    def test_validate_with_invalid_request(self):
        driver = MockPersistenceDriver()

        # Create request without query or command attribute
        request = type('Request', (), {})()

        assert driver.validate(request) is False


class TestSQLitePersistenceDriver:
    """Test SQLitePersistenceDriver implementation."""

    @patch('src.infrastructure.persistence.sqlite.sqlite_manager.SQLiteManager')
    def test_init_default_path(self, mock_sqlite_manager_class):
        mock_manager = Mock()
        mock_sqlite_manager_class.return_value = mock_manager

        driver = SQLitePersistenceDriver()

        assert driver.db_path == "cph_history.db"
        mock_sqlite_manager_class.assert_called_once_with("cph_history.db")

    @patch('src.infrastructure.persistence.sqlite.sqlite_manager.SQLiteManager')
    def test_init_custom_path(self, mock_sqlite_manager_class):
        mock_manager = Mock()
        mock_sqlite_manager_class.return_value = mock_manager

        driver = SQLitePersistenceDriver("custom.db")

        assert driver.db_path == "custom.db"
        mock_sqlite_manager_class.assert_called_once_with("custom.db")

    @patch('src.infrastructure.persistence.sqlite.sqlite_manager.SQLiteManager')
    def test_get_connection(self, mock_sqlite_manager_class):
        mock_manager = Mock()
        mock_connection = Mock()
        mock_manager.get_connection.return_value = mock_connection
        mock_sqlite_manager_class.return_value = mock_manager

        driver = SQLitePersistenceDriver()
        connection = driver.get_connection()

        assert connection is mock_connection
        mock_manager.get_connection.assert_called_once()

    @patch('src.infrastructure.persistence.sqlite.sqlite_manager.SQLiteManager')
    def test_execute_query(self, mock_sqlite_manager_class):
        mock_manager = Mock()
        expected_results = [{"id": 1, "value": "test"}]
        mock_manager.execute_query.return_value = expected_results
        mock_sqlite_manager_class.return_value = mock_manager

        driver = SQLitePersistenceDriver()
        results = driver.execute_query("SELECT * FROM test", (1,))

        assert results == expected_results
        mock_manager.execute_query.assert_called_once_with("SELECT * FROM test", (1,))

    @patch('src.infrastructure.persistence.sqlite.sqlite_manager.SQLiteManager')
    def test_execute_command(self, mock_sqlite_manager_class):
        mock_manager = Mock()
        mock_manager.execute_command.return_value = 3
        mock_sqlite_manager_class.return_value = mock_manager

        driver = SQLitePersistenceDriver()
        rows_affected = driver.execute_persistence_command("UPDATE test SET value = ?", ("new",))

        assert rows_affected == 3
        mock_manager.execute_command.assert_called_once_with("UPDATE test SET value = ?", ("new",))

    @patch('src.infrastructure.persistence.sqlite.sqlite_manager.SQLiteManager')
    def test_begin_transaction_success(self, mock_sqlite_manager_class):
        mock_manager = Mock()
        mock_connection = MagicMock()

        # Make get_connection return a context manager
        @contextmanager
        def mock_get_connection():
            yield mock_connection

        mock_manager.get_connection = mock_get_connection
        mock_sqlite_manager_class.return_value = mock_manager

        driver = SQLitePersistenceDriver()

        with driver.begin_transaction() as conn:
            assert conn is mock_connection

        # Rollback should not be called on success
        mock_connection.rollback.assert_not_called()


    @patch('src.infrastructure.persistence.sqlite.sqlite_manager.SQLiteManager')
    def test_get_repository_cached(self, mock_sqlite_manager_class):
        mock_manager = Mock()
        mock_sqlite_manager_class.return_value = mock_manager

        # Create a mock repository class
        class MockRepository:
            def __init__(self, manager):
                self.manager = manager

        driver = SQLitePersistenceDriver()

        # First call should create new instance
        repo1 = driver.get_repository(MockRepository)
        assert isinstance(repo1, MockRepository)
        assert repo1.manager is mock_manager

        # Second call should return cached instance
        repo2 = driver.get_repository(MockRepository)
        assert repo1 is repo2

    @patch('src.infrastructure.persistence.sqlite.sqlite_manager.SQLiteManager')
    def test_get_repository_different_classes(self, mock_sqlite_manager_class):
        mock_manager = Mock()
        mock_sqlite_manager_class.return_value = mock_manager

        class MockRepository1:
            def __init__(self, manager):
                self.manager = manager

        class MockRepository2:
            def __init__(self, manager):
                self.manager = manager

        driver = SQLitePersistenceDriver()

        repo1 = driver.get_repository(MockRepository1)
        repo2 = driver.get_repository(MockRepository2)

        # Different repository classes should get different instances
        assert repo1 is not repo2
        assert isinstance(repo1, MockRepository1)
        assert isinstance(repo2, MockRepository2)

    @patch('src.infrastructure.persistence.sqlite.sqlite_manager.SQLiteManager')
    def test_initialize(self, mock_sqlite_manager_class):
        mock_manager = Mock()
        mock_sqlite_manager_class.return_value = mock_manager

        driver = SQLitePersistenceDriver()
        # initialize should not raise any errors
        driver.initialize()

    @patch('src.infrastructure.persistence.sqlite.sqlite_manager.SQLiteManager')
    def test_cleanup(self, mock_sqlite_manager_class):
        mock_manager = Mock()
        mock_sqlite_manager_class.return_value = mock_manager

        class MockRepository:
            def __init__(self, manager):
                pass

        driver = SQLitePersistenceDriver()

        # Add some repositories
        driver.get_repository(MockRepository)
        assert len(driver._repositories) == 1

        # Cleanup should clear repositories
        driver.cleanup()
        assert len(driver._repositories) == 0
