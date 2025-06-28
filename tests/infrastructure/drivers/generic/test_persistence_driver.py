"""Tests for persistence driver"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from src.infrastructure.drivers.generic.persistence_driver import SQLitePersistenceDriver


class TestSQLitePersistenceDriver:
    """Test suite for SQLite persistence driver"""
    
    def setup_method(self):
        """Set up test driver before each test"""
        with patch('src.infrastructure.drivers.generic.persistence_driver.SQLiteManager') as mock_sqlite_manager_class:
            self.mock_sqlite_manager = Mock()
            mock_sqlite_manager_class.return_value = self.mock_sqlite_manager
            self.driver = SQLitePersistenceDriver("test.db")
    
    def test_initialization(self):
        """Test driver initialization"""
        assert self.driver.db_path == "test.db"
        assert hasattr(self.driver, '_sqlite_manager')
        assert self.driver._repositories == {}
    
    def test_get_connection(self):
        """Test getting database connection"""
        mock_connection = Mock()
        self.mock_sqlite_manager.get_connection.return_value = mock_connection
        
        result = self.driver.get_connection()
        
        assert result == mock_connection
        self.mock_sqlite_manager.get_connection.assert_called_once()
    
    def test_execute_query(self):
        """Test executing SELECT query"""
        expected_results = [{"id": 1, "name": "test"}]
        self.mock_sqlite_manager.execute_query.return_value = expected_results
        
        result = self.driver.execute_query("SELECT * FROM test", ("param1",))
        
        assert result == expected_results
        self.mock_sqlite_manager.execute_query.assert_called_once_with("SELECT * FROM test", ("param1",))
    
    def test_execute_persistence_command(self):
        """Test executing INSERT/UPDATE/DELETE command"""
        self.mock_sqlite_manager.execute_command.return_value = 1
        
        result = self.driver.execute_persistence_command("INSERT INTO test VALUES (?)", ("value",))
        
        assert result == 1
        self.mock_sqlite_manager.execute_command.assert_called_once_with("INSERT INTO test VALUES (?)", ("value",))
    
    def test_begin_transaction(self):
        """Test transaction context manager"""
        mock_conn = MagicMock()
        mock_context = MagicMock()
        mock_context.__enter__ = MagicMock(return_value=mock_conn)
        mock_context.__exit__ = MagicMock(return_value=None)
        self.mock_sqlite_manager.get_connection.return_value = mock_context
        
        with self.driver.begin_transaction() as conn:
            assert conn == mock_conn
    
    def test_get_repository(self):
        """Test getting repository instance"""
        class TestRepository:
            def __init__(self, manager):
                self.manager = manager
        
        repo = self.driver.get_repository(TestRepository)
        
        assert isinstance(repo, TestRepository)
        assert repo.manager == self.mock_sqlite_manager
        # Second call should return cached instance
        repo2 = self.driver.get_repository(TestRepository)
        assert repo is repo2
    
    def test_execute_command_with_query(self):
        """Test execute_command with query request"""
        mock_request = Mock()
        mock_request.query = "SELECT * FROM test"
        mock_request.params = ()
        
        expected_result = [{"id": 1}]
        self.mock_sqlite_manager.execute_query.return_value = expected_result
        
        result = self.driver.execute_command(mock_request)
        
        assert result == expected_result
    
    def test_execute_command_with_command(self):
        """Test execute_command with command request"""
        mock_request = Mock()
        mock_request.command = "INSERT INTO test VALUES (?)"
        mock_request.params = ("value",)
        del mock_request.query  # Ensure query attribute doesn't exist
        
        self.mock_sqlite_manager.execute_command.return_value = 1
        
        result = self.driver.execute_command(mock_request)
        
        assert result == 1
    
    def test_validate_with_query(self):
        """Test validate method with query request"""
        mock_request = Mock()
        mock_request.query = "SELECT * FROM test"
        
        assert self.driver.validate(mock_request) is True
    
    def test_validate_with_command(self):
        """Test validate method with command request"""
        mock_request = Mock()
        mock_request.command = "INSERT INTO test VALUES (?)"
        del mock_request.query  # Ensure query attribute doesn't exist
        
        assert self.driver.validate(mock_request) is True
    
    def test_validate_invalid_request(self):
        """Test validate method with invalid request"""
        mock_request = Mock()
        # Remove both query and command attributes
        if hasattr(mock_request, 'query'):
            del mock_request.query
        if hasattr(mock_request, 'command'):
            del mock_request.command
        
        assert self.driver.validate(mock_request) is False