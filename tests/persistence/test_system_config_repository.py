"""Tests for SystemConfigRepository."""
import json
from unittest.mock import MagicMock, patch

import pytest

from src.infrastructure.persistence.sqlite.repositories.system_config_repository import SystemConfigRepository


class MockRow:
    """Mock SQLite row for testing."""
    def __init__(self, data):
        self.data = data
    def keys(self):
        return self.data.keys()
    def __iter__(self):
        return iter(self.data.items())
    def __getitem__(self, key):
        return self.data[key]


class TestSystemConfigRepository:
    """Test SystemConfigRepository functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_manager = MagicMock()
        self.mock_config_manager = MagicMock()
        self.mock_connection = MagicMock()
        self.mock_cursor = MagicMock()

        # Setup connection context manager
        self.mock_manager.get_connection.return_value = self.mock_manager
        self.mock_manager.__enter__.return_value = self.mock_connection
        self.mock_manager.__exit__.return_value = None

        # Setup config_manager to return None for default values
        self.mock_config_manager.resolve_config.return_value = None

        self.repository = SystemConfigRepository(self.mock_manager, self.mock_config_manager)

    def test_init(self):
        """Test repository initialization."""
        assert self.repository.persistence_manager == self.mock_manager

    def test_create_with_all_fields(self):
        """Test create method with all fields."""
        entity = {
            'config_key': 'test_key',
            'config_value': 'test_value',
            'category': 'test_category',
            'description': 'test description'
        }

        with patch.object(self.repository, 'set_config') as mock_set:
            result = self.repository.create_config_record(entity)

        assert result == 'test_key'
        mock_set.assert_called_once_with('test_key', 'test_value', 'test_category', 'test description')

    def test_create_with_alternative_keys(self):
        """Test create method with alternative key names."""
        entity = {
            'key': 'alt_key',
            'value': 'alt_value'
        }

        with patch.object(self.repository, 'set_config') as mock_set:
            result = self.repository.create_config_record(entity)

        assert result == 'alt_key'
        mock_set.assert_called_once_with('alt_key', 'alt_value', None, None)

    def test_find_by_id(self):
        """Test find_by_id method."""
        expected_result = {'config_key': 'test', 'config_value': 'value'}

        with patch.object(self.repository, 'get_config_with_metadata', return_value=expected_result) as mock_get:
            result = self.repository.find_by_id('test')

        assert result == expected_result
        mock_get.assert_called_once_with('test')

    def test_find_all_with_pagination(self):
        """Test find_all method with pagination."""
        configs = [
            {'config_key': 'key1', 'config_value': 'value1'},
            {'config_key': 'key2', 'config_value': 'value2'},
            {'config_key': 'key3', 'config_value': 'value3'},
            {'config_key': 'key4', 'config_value': 'value4'}
        ]

        with patch.object(self.repository, 'get_all_configs_with_metadata', return_value=configs):
            # Test with limit only
            result = self.repository.find_all(limit=2, offset=None)
            assert len(result) == 2
            assert result[0]['config_key'] == 'key1'

            # Test with offset only
            result = self.repository.find_all(limit=None, offset=2)
            assert len(result) == 2
            assert result[0]['config_key'] == 'key3'

            # Test with both limit and offset
            result = self.repository.find_all(limit=1, offset=1)
            assert len(result) == 1
            assert result[0]['config_key'] == 'key2'

    def test_update_success(self):
        """Test successful update."""
        existing_config = {
            'config_key': 'test',
            'config_value': 'old_value',
            'category': 'old_category',
            'description': 'old description'
        }

        updates = {
            'config_value': 'new_value',
            'description': 'new description'
        }

        with patch.object(self.repository, 'get_config_with_metadata', return_value=existing_config), \
             patch.object(self.repository, 'set_config') as mock_set:
                result = self.repository.update('test', updates)

        assert result is True
        mock_set.assert_called_once_with('test', 'new_value', 'old_category', 'new description')

    def test_update_not_found(self):
        """Test update when config not found."""
        with patch.object(self.repository, 'get_config_with_metadata', return_value=None):
            result = self.repository.update('nonexistent', {'value': 'test'})

        assert result is False

    def test_delete(self):
        """Test delete method."""
        with patch.object(self.repository, 'delete_config', return_value=True) as mock_delete:
            result = self.repository.delete('test_key')

        assert result is True
        mock_delete.assert_called_once_with('test_key')

    def test_set_config_new_config(self):
        """Test setting new configuration."""
        # Mock existing config check to return None (new config)
        with patch.object(self.repository, 'get_config_with_metadata', return_value=None):
            self.mock_connection.execute.return_value = self.mock_cursor

            self.repository.set_config('new_key', 'new_value', 'category', 'description')

            # Verify INSERT query was called
            self.mock_connection.execute.assert_called_once()
            call_args = self.mock_connection.execute.call_args

            assert 'INSERT INTO system_config' in call_args[0][0]
            assert call_args[0][1] == ('new_key', '"new_value"', 'category', 'description')

    def test_set_config_update_existing(self):
        """Test updating existing configuration."""
        existing_config = {'config_key': 'existing', 'config_value': 'old'}

        with patch.object(self.repository, 'get_config_with_metadata', return_value=existing_config):
            self.mock_connection.execute.return_value = self.mock_cursor

            self.repository.set_config('existing', 'updated_value', 'new_category', 'updated_description')

            # Verify UPDATE query was called
            self.mock_connection.execute.assert_called_once()
            call_args = self.mock_connection.execute.call_args

            assert 'UPDATE system_config' in call_args[0][0]
            assert call_args[0][1] == ('"updated_value"', 'new_category', 'updated_description', 'existing')

    def test_set_config_none_value(self):
        """Test setting None value."""
        with patch.object(self.repository, 'get_config_with_metadata', return_value=None):
            self.mock_connection.execute.return_value = self.mock_cursor

            self.repository.set_config('null_key', None, 'test_category', 'test_description')

            call_args = self.mock_connection.execute.call_args
            assert call_args[0][1][1] is None  # config_value should be None

    def test_get_config_success(self):
        """Test successful get_config."""
        self.mock_cursor.fetchone.return_value = ('"test_value"',)
        self.mock_connection.execute.return_value = self.mock_cursor

        result = self.repository.get_config('test_key')

        assert result == 'test_value'

    def test_get_config_not_found(self):
        """Test get_config when config not found."""
        self.mock_cursor.fetchone.return_value = None
        self.mock_connection.execute.return_value = self.mock_cursor

        result = self.repository.get_config('nonexistent')

        assert result is None

    def test_get_config_json_decode_error(self):
        """Test get_config with JSON decode error."""
        self.mock_cursor.fetchone.return_value = ('invalid_json',)
        self.mock_connection.execute.return_value = self.mock_cursor

        result = self.repository.get_config('test_key')

        # Should return raw value when JSON decode fails
        assert result == 'invalid_json'

    def test_get_config_with_metadata_success(self):
        """Test successful get_config_with_metadata."""
        row_data = {
            'config_key': 'test',
            'config_value': '"test_value"',
            'category': 'test_cat',
            'description': 'test desc'
        }

        # Create a mock row that supports dict() conversion
        mock_row = MockRow(row_data)

        self.mock_cursor.fetchone.return_value = mock_row
        self.mock_connection.execute.return_value = self.mock_cursor

        result = self.repository.get_config_with_metadata('test')

        # Verify the config_value was parsed from JSON
        assert result['config_value'] == 'test_value'

    def test_get_config_with_metadata_not_found(self):
        """Test get_config_with_metadata when not found."""
        self.mock_cursor.fetchone.return_value = None
        self.mock_connection.execute.return_value = self.mock_cursor

        result = self.repository.get_config_with_metadata('nonexistent')

        assert result is None

    def test_get_configs_by_category(self):
        """Test get_configs_by_category."""
        row1 = {'config_key': 'key1', 'config_value': '"value1"'}
        row2 = {'config_key': 'key2', 'config_value': '"value2"'}

        mock_rows = [MockRow(row1), MockRow(row2)]

        self.mock_cursor.fetchall.return_value = mock_rows
        self.mock_connection.execute.return_value = self.mock_cursor

        result = self.repository.get_configs_by_category('test_category')

        assert len(result) == 2
        assert result[0]['config_value'] == 'value1'
        assert result[1]['config_value'] == 'value2'

    def test_get_all_configs(self):
        """Test get_all_configs."""
        mock_data = [
            ('key1', '"value1"'),
            ('key2', 'invalid_json'),
            ('key3', '"value3"')
        ]

        self.mock_cursor.fetchall.return_value = mock_data
        self.mock_connection.execute.return_value = self.mock_cursor

        result = self.repository.get_all_configs()

        assert result['key1'] == 'value1'
        assert result['key2'] == 'invalid_json'  # Should keep raw value
        assert result['key3'] == 'value3'

    def test_get_all_configs_with_metadata(self):
        """Test get_all_configs_with_metadata."""
        row_data = {'config_key': 'test', 'config_value': '"test_value"'}

        mock_row = MockRow(row_data)

        self.mock_cursor.fetchall.return_value = [mock_row]
        self.mock_connection.execute.return_value = self.mock_cursor

        result = self.repository.get_all_configs_with_metadata()

        assert len(result) == 1
        assert result[0]['config_value'] == 'test_value'

    def test_delete_config_success(self):
        """Test successful delete_config."""
        self.mock_cursor.rowcount = 1
        self.mock_connection.execute.return_value = self.mock_cursor

        result = self.repository.delete_config('test_key')

        assert result is True

    def test_delete_config_not_found(self):
        """Test delete_config when key not found."""
        self.mock_cursor.rowcount = 0
        self.mock_connection.execute.return_value = self.mock_cursor

        result = self.repository.delete_config('nonexistent')

        assert result is False

    def test_bulk_set_configs(self):
        """Test bulk_set_configs."""
        configs = {
            'key1': 'value1',
            'key2': 'value2'
        }

        with patch.object(self.repository, 'set_config') as mock_set:
            self.repository.bulk_set_configs(configs, 'test_category')

        assert mock_set.call_count == 2
        mock_set.assert_any_call('key1', 'value1', 'test_category', None)
        mock_set.assert_any_call('key2', 'value2', 'test_category', None)

    def test_get_user_specified_configs(self):
        """Test get_user_specified_configs."""
        mock_data = [
            ('command', '"test"'),
            ('language', '"python"')
        ]

        self.mock_cursor.fetchall.return_value = mock_data
        self.mock_connection.execute.return_value = self.mock_cursor

        result = self.repository.get_user_specified_configs()

        assert result['command'] == 'test'
        assert result['language'] == 'python'

    def test_get_execution_context_summary(self):
        """Test get_execution_context_summary."""
        mock_data = [
            ('command', '"test"', 1),
            ('language', None, 0),
            ('env_type', '"local"', 1)
        ]

        self.mock_cursor.fetchall.return_value = mock_data
        self.mock_connection.execute.return_value = self.mock_cursor

        result = self.repository.get_execution_context_summary()

        assert result['values']['command'] == 'test'
        assert result['values']['language'] is None
        assert result['values']['env_type'] == 'local'
        assert result['user_specified']['command'] is True
        assert result['user_specified']['language'] is False
        assert result['user_specified']['env_type'] is True

    def test_search_configs(self):
        """Test search_configs."""
        row_data = {
            'config_key': 'test_key',
            'config_value': '"test_value"',
            'description': 'test description'
        }

        mock_row = MockRow(row_data)

        self.mock_cursor.fetchall.return_value = [mock_row]
        self.mock_connection.execute.return_value = self.mock_cursor

        result = self.repository.search_configs('test')

        assert len(result) == 1
        assert result[0]['config_value'] == 'test_value'

        # Verify search pattern was used correctly
        call_args = self.mock_connection.execute.call_args
        assert call_args[0][1] == ('%test%', '%test%')

    def test_search_configs_with_null_value(self):
        """Test search_configs with null config_value."""
        row_data = {
            'config_key': 'test_key',
            'config_value': None,
            'description': 'test description'
        }

        mock_row = MockRow(row_data)

        self.mock_cursor.fetchall.return_value = [mock_row]
        self.mock_connection.execute.return_value = self.mock_cursor

        result = self.repository.search_configs('test')

        assert len(result) == 1
        assert result[0]['config_value'] is None

    def test_get_categories(self):
        """Test get_categories."""
        mock_data = [
            ('category1',),
            ('category2',),
            ('category3',)
        ]

        self.mock_cursor.fetchall.return_value = mock_data
        self.mock_connection.execute.return_value = self.mock_cursor

        result = self.repository.get_categories()

        assert result == ['category1', 'category2', 'category3']
