"""Tests for SQLite-based SystemConfigRepository."""
import pytest
from unittest.mock import Mock, MagicMock, patch
import json
from contextlib import contextmanager

from src.configuration.system_config_repository import SystemConfigRepository


class MockSQLiteRow:
    """Mock SQLite row that behaves like a real row object."""
    def __init__(self, data):
        self._data = data
    
    def keys(self):
        return self._data.keys()
    
    def __getitem__(self, key):
        if isinstance(key, int):
            # Support numeric indexing for tuple-like behavior
            values = list(self._data.values())
            return values[key] if key < len(values) else None
        return self._data.get(key)
    
    def __iter__(self):
        return iter(self._data.values())


class TestSystemConfigRepositorySQLite:
    """Test cases for SystemConfigRepository with SQLite backend."""
    
    @pytest.fixture
    def mock_sqlite_manager(self):
        """Create a mock SQLite manager."""
        mock = Mock()
        return mock
    
    @pytest.fixture
    def mock_config_manager(self):
        """Create a mock config manager."""
        mock = Mock()
        return mock
    
    @pytest.fixture
    def mock_connection(self):
        """Create a mock database connection with context manager support."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.execute.return_value = mock_cursor
        mock_conn.__enter__ = MagicMock(return_value=mock_conn)
        mock_conn.__exit__ = MagicMock(return_value=None)
        return mock_conn
    
    @pytest.fixture
    def repository(self, mock_sqlite_manager, mock_config_manager, mock_connection):
        """Create a repository instance with mocked dependencies."""
        # Mock the get_connection method to return our mock connection
        mock_sqlite_manager.get_connection.return_value = mock_connection
        repo = SystemConfigRepository(mock_sqlite_manager, mock_config_manager)
        return repo
    
    # Test initialization
    def test_init(self, mock_sqlite_manager, mock_config_manager):
        """Test repository initialization."""
        repo = SystemConfigRepository(mock_sqlite_manager, mock_config_manager)
        assert repo.config_manager == mock_config_manager
        # Check parent class initialization by verifying persistence_manager is set
        assert repo.persistence_manager == mock_sqlite_manager
    
    # Test create_entity_record
    def test_create_entity_record_with_config_key(self, repository, mock_connection):
        """Test creating entity with config_key."""
        entity = {
            'config_key': 'test_key',
            'config_value': 'test_value',
            'category': 'test_category',
            'description': 'test description'
        }
        
        # Mock get_config_with_metadata to return None (new config)
        mock_cursor = mock_connection.execute.return_value
        mock_cursor.fetchone.return_value = None
        
        result = repository.create_entity_record(entity)
        
        assert result == 'test_key'
        # Verify set_config was called (through SQL execution)
        assert mock_connection.execute.called
    
    def test_create_entity_record_with_key(self, repository, mock_connection):
        """Test creating entity with 'key' instead of 'config_key'."""
        entity = {
            'key': 'test_key',
            'value': 'test_value'
        }
        
        # Mock get_config_with_metadata to return None (new config)
        mock_cursor = mock_connection.execute.return_value
        mock_cursor.fetchone.return_value = None
        
        result = repository.create_entity_record(entity)
        
        assert result == 'test_key'
        assert mock_connection.execute.called
    
    def test_create_entity_record_with_config_defaults(self, repository, mock_config_manager, mock_connection):
        """Test creating entity with defaults from config manager."""
        entity = {
            'config_key': 'test_key',
            'config_value': 'test_value'
        }
        
        # Mock config manager responses
        mock_config_manager.resolve_config.side_effect = [
            'default_category',
            'default_description'
        ]
        
        # Mock get_config_with_metadata to return None (new config)
        mock_cursor = mock_connection.execute.return_value
        mock_cursor.fetchone.return_value = None
        
        result = repository.create_entity_record(entity)
        
        assert result == 'test_key'
        assert mock_config_manager.resolve_config.call_count == 2
    
    # Test find_by_id
    def test_find_by_id_found(self, repository, mock_connection):
        """Test finding config by ID when it exists."""
        mock_cursor = mock_connection.execute.return_value
        mock_cursor.fetchone.return_value = MockSQLiteRow({
            'config_key': 'test_key',
            'config_value': '"test_value"',
            'category': 'test_category',
            'description': 'test description'
        })
        
        result = repository.find_by_id('test_key')
        
        assert result is not None
        assert result['config_key'] == 'test_key'
        mock_connection.execute.assert_called()
    
    def test_find_by_id_not_found(self, repository, mock_connection):
        """Test finding config by ID when it doesn't exist."""
        mock_cursor = mock_connection.execute.return_value
        mock_cursor.fetchone.return_value = None
        
        result = repository.find_by_id('non_existent')
        
        assert result is None
    
    # Test find_all
    def test_find_all_with_limit_offset(self, repository, mock_connection):
        """Test finding all configs with limit and offset."""
        mock_cursor = mock_connection.execute.return_value
        mock_cursor.fetchall.return_value = [
            MockSQLiteRow({'config_key': 'key1', 'config_value': '"value1"'}),
            MockSQLiteRow({'config_key': 'key2', 'config_value': '"value2"'}),
            MockSQLiteRow({'config_key': 'key3', 'config_value': '"value3"'}),
        ]
        
        result = repository.find_all(limit=2, offset=1)
        
        # Should return items 2 and 3 (offset=1, limit=2)
        assert len(result) == 2
        assert result[0]['config_key'] == 'key2'
        assert result[1]['config_key'] == 'key3'
    
    # Test update
    def test_update_existing(self, repository, mock_connection):
        """Test updating existing config."""
        # Mock finding existing config
        mock_cursor = mock_connection.execute.return_value
        mock_cursor.fetchone.return_value = MockSQLiteRow({
            'config_key': 'test_key',
            'config_value': '"old_value"',
            'category': 'old_category',
            'description': 'old_description'
        })
        
        updates = {
            'config_value': 'new_value',
            'category': 'new_category'
        }
        
        result = repository.update('test_key', updates)
        
        assert result is True
        # Should execute both SELECT and UPDATE queries
        assert mock_connection.execute.call_count >= 2
    
    def test_update_non_existing(self, repository, mock_connection):
        """Test updating non-existing config."""
        mock_cursor = mock_connection.execute.return_value
        mock_cursor.fetchone.return_value = None
        
        updates = {'config_value': 'new_value'}
        
        result = repository.update('non_existent', updates)
        
        assert result is False
    
    # Test delete
    def test_delete_existing(self, repository, mock_connection):
        """Test deleting existing config."""
        mock_cursor = mock_connection.execute.return_value
        mock_cursor.rowcount = 1
        
        result = repository.delete('test_key')
        
        assert result is True
        mock_connection.execute.assert_called()
    
    def test_delete_non_existing(self, repository, mock_connection):
        """Test deleting non-existing config."""
        mock_cursor = mock_connection.execute.return_value
        mock_cursor.rowcount = 0
        
        result = repository.delete('non_existent')
        
        assert result is False
    
    # Test set_config
    def test_set_config_new(self, repository, mock_connection):
        """Test setting new config."""
        mock_cursor = mock_connection.execute.return_value
        # First query (check existence) returns None
        mock_cursor.fetchone.return_value = None
        
        repository.set_config('new_key', {'data': 'value'}, 'category', 'description')
        
        # Should execute SELECT then INSERT
        assert mock_connection.execute.call_count == 2
        insert_call = mock_connection.execute.call_args_list[1]
        assert 'INSERT INTO system_config' in insert_call[0][0]
    
    def test_set_config_update(self, repository, mock_connection):
        """Test updating existing config."""
        mock_cursor = mock_connection.execute.return_value
        # First query returns existing config
        mock_cursor.fetchone.return_value = MockSQLiteRow({
            'config_key': 'existing_key',
            'config_value': '"old_value"'
        })
        
        repository.set_config('existing_key', 'new_value', None, None)
        
        # Should execute SELECT then UPDATE
        assert mock_connection.execute.call_count == 2
        update_call = mock_connection.execute.call_args_list[1]
        assert 'UPDATE system_config' in update_call[0][0]
    
    def test_set_config_null_value(self, repository, mock_connection):
        """Test setting config with None value."""
        mock_cursor = mock_connection.execute.return_value
        mock_cursor.fetchone.return_value = None
        
        repository.set_config('null_key', None, None, None)
        
        # Should store None as NULL in database
        insert_call = mock_connection.execute.call_args_list[1]
        params = insert_call[0][1]
        assert params[1] is None  # config_value should be None
    
    # Test get_config
    def test_get_config_json_value(self, repository, mock_connection):
        """Test getting config with JSON value."""
        mock_cursor = mock_connection.execute.return_value
        mock_cursor.fetchone.return_value = ('{"key": "value"}',)
        
        result = repository.get_config('test_key')
        
        assert result == {'key': 'value'}
    
    def test_get_config_plain_value(self, repository, mock_connection):
        """Test getting config with plain string value."""
        mock_cursor = mock_connection.execute.return_value
        mock_cursor.fetchone.return_value = ('plain_string',)
        
        result = repository.get_config('test_key')
        
        assert result == 'plain_string'
    
    def test_get_config_not_found(self, repository, mock_connection):
        """Test getting non-existing config."""
        mock_cursor = mock_connection.execute.return_value
        mock_cursor.fetchone.return_value = None
        
        result = repository.get_config('non_existent')
        
        assert result is None
    
    # Test get_configs_by_category
    def test_get_configs_by_category(self, repository, mock_connection):
        """Test getting configs by category."""
        mock_cursor = mock_connection.execute.return_value
        mock_cursor.fetchall.return_value = [
            MockSQLiteRow({'config_key': 'key1', 'config_value': '"value1"', 'category': 'test'}),
            MockSQLiteRow({'config_key': 'key2', 'config_value': '"value2"', 'category': 'test'})
        ]
        
        result = repository.get_configs_by_category('test')
        
        assert len(result) == 2
        assert all(config['category'] == 'test' for config in result)
    
    # Test get_all_configs
    def test_get_all_configs(self, repository, mock_connection):
        """Test getting all configs as dictionary."""
        mock_cursor = mock_connection.execute.return_value
        mock_cursor.fetchall.return_value = [
            ('key1', '"value1"'),
            ('key2', '"value2"'),
            ('key3', 'plain_value')
        ]
        
        result = repository.get_all_configs()
        
        assert result == {
            'key1': 'value1',
            'key2': 'value2',
            'key3': 'plain_value'
        }
    
    # Test bulk_set_configs
    def test_bulk_set_configs(self, repository, mock_connection):
        """Test setting multiple configs at once."""
        configs = {
            'key1': 'value1',
            'key2': {'nested': 'value2'},
            'key3': None
        }
        
        # Mock get_config_with_metadata to return None for all keys
        mock_cursor = mock_connection.execute.return_value
        mock_cursor.fetchone.return_value = None
        
        repository.bulk_set_configs(configs, 'bulk_category')
        
        # Should call set_config for each key
        # Each set_config does SELECT + INSERT/UPDATE = 2 calls per config
        assert mock_connection.execute.call_count == 6  # 3 configs * 2 calls each
    
    # Test get_user_specified_configs
    def test_get_user_specified_configs(self, repository, mock_connection):
        """Test getting user-specified configs."""
        mock_cursor = mock_connection.execute.return_value
        mock_cursor.fetchall.return_value = [
            ('command', '"python test.py"'),
            ('language', '"python"')
        ]
        
        result = repository.get_user_specified_configs()
        
        assert result == {
            'command': 'python test.py',
            'language': 'python'
        }
        
        # Check that query filters for specific keys
        query_call = mock_connection.execute.call_args[0][0]
        assert 'command' in query_call
        assert 'language' in query_call
        assert 'env_type' in query_call
    
    # Test get_execution_context_summary
    def test_get_execution_context_summary(self, repository, mock_connection):
        """Test getting execution context summary."""
        mock_cursor = mock_connection.execute.return_value
        mock_cursor.fetchall.return_value = [
            ('command', '"python test.py"', 1),
            ('language', None, 0),
            ('env_type', '"docker"', 1)
        ]
        
        result = repository.get_execution_context_summary()
        
        assert result['values'] == {
            'command': 'python test.py',
            'language': None,
            'env_type': 'docker'
        }
        assert result['user_specified'] == {
            'command': True,
            'language': False,
            'env_type': True
        }
    
    # Test search_configs
    def test_search_configs(self, repository, mock_connection):
        """Test searching configs."""
        mock_cursor = mock_connection.execute.return_value
        mock_cursor.fetchall.return_value = [
            MockSQLiteRow({
                'config_key': 'test_key',
                'config_value': '"test_value"',
                'description': 'contains test term'
            })
        ]
        
        result = repository.search_configs('test')
        
        assert len(result) == 1
        assert result[0]['config_key'] == 'test_key'
        
        # Check search pattern in query
        query_call = mock_connection.execute.call_args
        assert query_call[0][1] == ('%test%', '%test%')
    
    # Test get_categories
    def test_get_categories(self, repository, mock_connection):
        """Test getting unique categories."""
        mock_cursor = mock_connection.execute.return_value
        mock_cursor.fetchall.return_value = [
            ('category1',),
            ('category2',),
            ('category3',)
        ]
        
        result = repository.get_categories()
        
        assert result == ['category1', 'category2', 'category3']
        
        # Check that query uses DISTINCT
        query_call = mock_connection.execute.call_args[0][0]
        assert 'DISTINCT category' in query_call
    
    # Test error handling
    def test_get_config_with_metadata_json_decode_error(self, repository, mock_connection):
        """Test handling JSON decode error in get_config_with_metadata."""
        mock_cursor = mock_connection.execute.return_value
        mock_cursor.fetchone.return_value = MockSQLiteRow({
            'config_key': 'test_key',
            'config_value': 'invalid{json'
        })
        
        result = repository.get_config_with_metadata('test_key')
        
        # Should return raw value when JSON decode fails
        assert result['config_value'] == 'invalid{json'
    
    def test_create_config_record(self, repository, mock_connection):
        """Test create_config_record method (duplicate of create_entity_record)."""
        entity = {
            'config_key': 'test_key',
            'config_value': 'test_value'
        }
        
        # Mock get_config_with_metadata to return None (new config)
        mock_cursor = mock_connection.execute.return_value
        mock_cursor.fetchone.return_value = None
        
        result = repository.create_config_record(entity)
        
        assert result == 'test_key'
        assert mock_connection.execute.called