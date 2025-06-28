"""Tests for ConfigurationRepository"""
import pytest
from pathlib import Path
from unittest.mock import Mock, MagicMock, call
from src.configuration.configuration_repository import ConfigurationRepository


class TestConfigurationRepository:
    """Test ConfigurationRepository class"""
    
    @pytest.fixture
    def mock_json_provider(self):
        """Create mock JSON provider"""
        provider = Mock()
        provider.loads = Mock(side_effect=lambda x: x)  # Simple passthrough
        provider.dumps = Mock(side_effect=lambda x: x)  # Simple passthrough
        return provider
    
    @pytest.fixture
    def mock_sqlite_provider(self):
        """Create mock SQLite provider"""
        provider = Mock()
        provider.connect = Mock()
        provider.close = Mock()
        provider.commit = Mock()
        provider.execute_sql_statement = Mock()
        provider.fetchone = Mock()
        provider.fetchall = Mock()
        return provider
    
    @pytest.fixture
    def repository(self, mock_json_provider, mock_sqlite_provider):
        """Create repository with mocked providers"""
        return ConfigurationRepository(
            db_path="/test/db.sqlite",
            json_provider=mock_json_provider,
            sqlite_provider=mock_sqlite_provider
        )
    
    def test_init(self):
        """Test initialization"""
        repo = ConfigurationRepository("/test/db.sqlite", None, None)
        assert repo.db_path == "/test/db.sqlite"
        assert repo._json_provider is not None
        assert repo._sqlite_provider is not None
    
    def test_init_with_providers(self, mock_json_provider, mock_sqlite_provider):
        """Test initialization with custom providers"""
        repo = ConfigurationRepository(
            "/test/db.sqlite",
            json_provider=mock_json_provider,
            sqlite_provider=mock_sqlite_provider
        )
        assert repo._json_provider == mock_json_provider
        assert repo._sqlite_provider == mock_sqlite_provider
    
    def test_load_previous_values_no_db(self, repository, monkeypatch):
        """Test loading previous values when database doesn't exist"""
        monkeypatch.setattr(Path, "exists", lambda self: False)
        
        result = repository.load_previous_values()
        
        assert result == {
            "old_contest_name": "",
            "old_problem_name": ""
        }
        repository._sqlite_provider.connect.assert_not_called()
    
    def test_load_previous_values_success(self, repository, mock_sqlite_provider, monkeypatch):
        """Test successfully loading previous values"""
        monkeypatch.setattr(Path, "exists", lambda self: True)
        
        # Mock database connection
        mock_conn = Mock()
        mock_sqlite_provider.connect.return_value = mock_conn
        
        # Mock cursor for queries
        mock_cursor = Mock()
        mock_sqlite_provider.execute_sql_statement.return_value = mock_cursor
        
        # Set up return values for fetchone
        mock_sqlite_provider.fetchone.side_effect = [
            ("ABC123",),  # old_contest_name
            ("problem_A",)  # old_problem_name
        ]
        
        result = repository.load_previous_values()
        
        assert result == {
            "old_contest_name": "ABC123",
            "old_problem_name": "problem_A"
        }
        
        # Verify database operations
        mock_sqlite_provider.connect.assert_called_once_with("/test/db.sqlite")
        assert mock_sqlite_provider.execute_sql_statement.call_count == 2
        mock_sqlite_provider.close.assert_called_once_with(mock_conn)
    
    def test_load_previous_values_null_values(self, repository, mock_sqlite_provider, monkeypatch):
        """Test loading when values are null in database"""
        monkeypatch.setattr(Path, "exists", lambda self: True)
        
        mock_conn = Mock()
        mock_sqlite_provider.connect.return_value = mock_conn
        mock_cursor = Mock()
        mock_sqlite_provider.execute_sql_statement.return_value = mock_cursor
        
        # Return None for both values
        mock_sqlite_provider.fetchone.side_effect = [None, None]
        
        result = repository.load_previous_values()
        
        assert result == {
            "old_contest_name": "",
            "old_problem_name": ""
        }
    
    def test_load_previous_values_exception(self, repository, mock_sqlite_provider, monkeypatch):
        """Test exception handling during load"""
        monkeypatch.setattr(Path, "exists", lambda self: True)
        
        mock_sqlite_provider.connect.side_effect = Exception("Database error")
        
        with pytest.raises(RuntimeError, match="Failed to load previous configuration values"):
            repository.load_previous_values()
    
    def test_save_current_values_no_db(self, repository, monkeypatch):
        """Test saving values when database doesn't exist"""
        monkeypatch.setattr(Path, "exists", lambda self: False)
        
        # Should return without error
        repository.save_current_values("ABC123", "problem_A")
        
        repository._sqlite_provider.connect.assert_not_called()
    
    def test_save_current_values_success(self, repository, mock_sqlite_provider, monkeypatch):
        """Test successfully saving current values"""
        monkeypatch.setattr(Path, "exists", lambda self: True)
        
        mock_conn = Mock()
        mock_sqlite_provider.connect.return_value = mock_conn
        mock_cursor = Mock()
        mock_sqlite_provider.execute_sql_statement.return_value = mock_cursor
        
        repository.save_current_values("ABC123", "problem_A")
        
        # Verify database operations
        mock_sqlite_provider.connect.assert_called_once_with("/test/db.sqlite")
        assert mock_sqlite_provider.execute_sql_statement.call_count == 2
        
        # Check the SQL calls
        calls = mock_sqlite_provider.execute_sql_statement.call_args_list
        assert calls[0][0][1] == """
            INSERT OR REPLACE INTO system_config (config_key, config_value)
            VALUES (?, ?)
        """
        assert calls[0][0][2] == ("old_contest_name", "ABC123")
        assert calls[1][0][2] == ("old_problem_name", "problem_A")
        
        mock_sqlite_provider.commit.assert_called_once_with(mock_conn)
        mock_sqlite_provider.close.assert_called_once_with(mock_conn)
    
    def test_save_current_values_exception(self, repository, mock_sqlite_provider, monkeypatch):
        """Test exception handling during save"""
        monkeypatch.setattr(Path, "exists", lambda self: True)
        
        mock_sqlite_provider.connect.side_effect = Exception("Database error")
        
        with pytest.raises(RuntimeError, match="Failed to save current configuration values"):
            repository.save_current_values("ABC123", "problem_A")
    
    def test_get_config_value_success(self, repository, mock_sqlite_provider):
        """Test getting a config value"""
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_sqlite_provider.execute_sql_statement.return_value = mock_cursor
        mock_sqlite_provider.fetchone.return_value = ("test_value",)
        
        result = repository._get_config_value(mock_conn, "test_key")
        
        assert result == "test_value"
        mock_sqlite_provider.execute_sql_statement.assert_called_once_with(
            mock_conn,
            "SELECT config_value FROM system_config WHERE config_key = ?",
            ("test_key",)
        )
    
    def test_get_config_value_not_found(self, repository, mock_sqlite_provider):
        """Test getting a config value that doesn't exist"""
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_sqlite_provider.execute_sql_statement.return_value = mock_cursor
        mock_sqlite_provider.fetchone.return_value = None
        
        result = repository._get_config_value(mock_conn, "test_key")
        
        assert result is None
    
    def test_get_config_value_json_error(self, repository, mock_sqlite_provider, mock_json_provider):
        """Test JSON parsing error when getting config value"""
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_sqlite_provider.execute_sql_statement.return_value = mock_cursor
        mock_sqlite_provider.fetchone.return_value = ("invalid_json",)
        mock_json_provider.loads.side_effect = ValueError("Invalid JSON")
        
        with pytest.raises(ValueError, match="Failed to parse configuration value"):
            repository._get_config_value(mock_conn, "test_key")
    
    def test_save_config_value(self, repository, mock_sqlite_provider, mock_json_provider):
        """Test saving a config value"""
        mock_conn = Mock()
        
        repository._save_config_value(mock_conn, "test_key", "test_value")
        
        mock_json_provider.dumps.assert_called_once_with("test_value")
        mock_sqlite_provider.execute_sql_statement.assert_called_once_with(
            mock_conn,
            """
            INSERT OR REPLACE INTO system_config (config_key, config_value)
            VALUES (?, ?)
        """,
            ("test_key", "test_value")
        )
    
    def test_get_available_config_keys_no_db(self, repository, monkeypatch):
        """Test getting available keys when database doesn't exist"""
        monkeypatch.setattr(Path, "exists", lambda self: False)
        
        result = repository.get_available_config_keys()
        
        assert result == []
        repository._sqlite_provider.connect.assert_not_called()
    
    def test_get_available_config_keys_success(self, repository, mock_sqlite_provider, monkeypatch):
        """Test successfully getting available config keys"""
        monkeypatch.setattr(Path, "exists", lambda self: True)
        
        mock_conn = Mock()
        mock_sqlite_provider.connect.return_value = mock_conn
        mock_cursor = Mock()
        mock_sqlite_provider.execute_sql_statement.return_value = mock_cursor
        mock_sqlite_provider.fetchall.return_value = [
            ("old_contest_name",),
            ("old_problem_name",),
            ("language",),
            ("environment",)
        ]
        
        result = repository.get_available_config_keys()
        
        assert result == ["old_contest_name", "old_problem_name", "language", "environment"]
        mock_sqlite_provider.execute_sql_statement.assert_called_once_with(
            mock_conn,
            "SELECT config_key FROM system_config",
            ()
        )
        mock_sqlite_provider.close.assert_called_once_with(mock_conn)
    
    def test_get_available_config_keys_exception(self, repository, mock_sqlite_provider, monkeypatch):
        """Test exception handling when getting available keys"""
        monkeypatch.setattr(Path, "exists", lambda self: True)
        
        mock_sqlite_provider.connect.side_effect = Exception("Database error")
        
        with pytest.raises(RuntimeError, match="Failed to retrieve available configuration keys"):
            repository.get_available_config_keys()
    
    def test_default_providers(self):
        """Test that default providers are created when None provided"""
        repo = ConfigurationRepository("/test/db.sqlite", None, None)
        
        # Check that providers exist and have expected methods
        assert hasattr(repo._json_provider, 'loads')
        assert hasattr(repo._json_provider, 'dumps')
        assert hasattr(repo._sqlite_provider, 'connect')
        assert hasattr(repo._sqlite_provider, 'close')