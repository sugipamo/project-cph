import pytest
from unittest.mock import Mock, patch, MagicMock
import json

from src.configuration.system_config_repository import SystemConfigRepository


class TestSystemConfigRepository:
    @pytest.fixture
    def mock_sqlite_manager(self):
        """Mock SQLite manager with connection context manager."""
        mock_manager = Mock()
        mock_connection = Mock()
        mock_manager.get_connection.return_value.__enter__ = Mock(return_value=mock_connection)
        mock_manager.get_connection.return_value.__exit__ = Mock(return_value=None)
        return mock_manager

    @pytest.fixture
    def mock_config_manager(self):
        """Mock configuration manager."""
        mock_manager = Mock()
        mock_manager.resolve_config.return_value = "default_value"
        return mock_manager

    @pytest.fixture
    def repository(self, mock_sqlite_manager, mock_config_manager):
        return SystemConfigRepository(mock_sqlite_manager, mock_config_manager)

    def test_init(self, mock_sqlite_manager, mock_config_manager):
        repo = SystemConfigRepository(mock_sqlite_manager, mock_config_manager)
        assert repo.persistence_manager == mock_sqlite_manager
        assert repo.config_manager == mock_config_manager

    def test_set_config_new(self, repository, mock_sqlite_manager):
        """Test setting a new configuration."""
        mock_conn = mock_sqlite_manager.get_connection.return_value.__enter__.return_value
        
        # Mock that key doesn't exist
        repository.get_config_with_metadata = Mock(return_value=None)
        
        repository.set_config("test_key", {"value": 123}, "test_category", "Test description")
        
        # Should execute INSERT query
        mock_conn.execute.assert_called_once()
        query = mock_conn.execute.call_args[0][0]
        assert "INSERT INTO system_config" in query

    def test_set_config_update(self, repository, mock_sqlite_manager):
        """Test updating existing configuration."""
        mock_conn = mock_sqlite_manager.get_connection.return_value.__enter__.return_value
        
        # Mock that key exists
        repository.get_config_with_metadata = Mock(return_value={"config_key": "test_key"})
        
        repository.set_config("test_key", {"value": 456}, "test_category", "Updated description")
        
        # Should execute UPDATE query
        mock_conn.execute.assert_called_once()
        query = mock_conn.execute.call_args[0][0]
        assert "UPDATE system_config" in query

    def test_get_config_exists(self, repository, mock_sqlite_manager):
        """Test getting existing configuration."""
        mock_conn = mock_sqlite_manager.get_connection.return_value.__enter__.return_value
        mock_cursor = Mock()
        mock_conn.execute.return_value = mock_cursor
        mock_cursor.fetchone.return_value = ('{"key": "value"}',)
        
        result = repository.get_config("test_key")
        
        assert result == {"key": "value"}
        mock_conn.execute.assert_called_once()
        query = mock_conn.execute.call_args[0][0]
        assert "SELECT config_value FROM system_config" in query

    def test_get_config_not_exists(self, repository, mock_sqlite_manager):
        """Test getting non-existent configuration."""
        mock_conn = mock_sqlite_manager.get_connection.return_value.__enter__.return_value
        mock_cursor = Mock()
        mock_conn.execute.return_value = mock_cursor
        mock_cursor.fetchone.return_value = None
        
        result = repository.get_config("non_existent_key")
        
        assert result is None

    def test_get_config_with_metadata(self, repository, mock_sqlite_manager):
        """Test getting configuration with metadata."""
        mock_conn = mock_sqlite_manager.get_connection.return_value.__enter__.return_value
        mock_cursor = Mock()
        mock_conn.execute.return_value = mock_cursor
        
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
        
        mock_row = MockRow({
            'config_key': 'test_key',
            'config_value': '{"data": "test"}',
            'category': 'test_category',
            'description': 'Test description'
        })
        mock_cursor.fetchone.return_value = mock_row
        
        result = repository.get_config_with_metadata("test_key")
        
        assert result is not None
        assert result['config_key'] == 'test_key'
        assert result['config_value'] == {"data": "test"}

    def test_get_configs_by_category(self, repository, mock_sqlite_manager):
        """Test getting all configs in a category."""
        mock_conn = mock_sqlite_manager.get_connection.return_value.__enter__.return_value
        mock_cursor = Mock()
        mock_conn.execute.return_value = mock_cursor
        
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
        
        mock_row1 = MockRow({
            'config_key': 'key1',
            'config_value': '{"val": 1}',
            'category': 'test'
        })
        
        mock_row2 = MockRow({
            'config_key': 'key2',
            'config_value': '{"val": 2}',
            'category': 'test'
        })
        
        mock_cursor.fetchall.return_value = [mock_row1, mock_row2]
        
        result = repository.get_configs_by_category("test")
        
        assert len(result) == 2
        assert result[0]['config_key'] == 'key1'
        assert result[1]['config_key'] == 'key2'

    def test_delete_config(self, repository, mock_sqlite_manager):
        """Test deleting a configuration."""
        mock_conn = mock_sqlite_manager.get_connection.return_value.__enter__.return_value
        mock_cursor = Mock()
        mock_conn.execute.return_value = mock_cursor
        mock_cursor.rowcount = 1
        
        repository.delete_config("test_key")
        
        mock_conn.execute.assert_called_once()
        query = mock_conn.execute.call_args[0][0]
        assert "DELETE FROM system_config" in query

    def test_create_entity_record(self, repository):
        """Test creating entity record."""
        repository.set_config = Mock()
        
        entity = {
            'config_key': 'test_key',
            'config_value': 'test_value',
            'category': 'test_category',
            'description': 'Test description'
        }
        
        result = repository.create_entity_record(entity)
        
        assert result == 'test_key'
        repository.set_config.assert_called_once_with(
            'test_key', 'test_value', 'test_category', 'Test description'
        )