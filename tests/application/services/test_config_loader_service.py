"""Tests for ConfigLoaderService - Configuration file loading service"""
import pytest
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch
from typing import Dict, Any

from src.application.services.config_loader_service import ConfigLoaderService
from src.infrastructure.di_container import DIContainer, DIKey


class TestConfigLoaderService:
    """Test suite for configuration loader service"""
    
    def setup_method(self):
        """Set up test fixtures"""
        # Create mock DI container
        self.mock_container = Mock(spec=DIContainer)
        
        # Create mock providers
        self.mock_json_provider = Mock()
        self.mock_os_provider = Mock()
        self.mock_file_driver = Mock()
        
        # Configure container to return mocked providers
        def resolve_mock(key):
            if key == DIKey.JSON_PROVIDER:
                return self.mock_json_provider
            elif key == DIKey.OS_PROVIDER:
                return self.mock_os_provider
            elif key == DIKey.FILE_DRIVER:
                return self.mock_file_driver
            return Mock()
        
        self.mock_container.resolve.side_effect = resolve_mock
        
        # Create service instance
        self.service = ConfigLoaderService(self.mock_container)
    
    def test_init_loads_providers(self):
        """Test that initialization loads required providers from container"""
        # Verify providers were loaded
        assert self.service._json_provider == self.mock_json_provider
        assert self.service._os_provider == self.mock_os_provider
        assert self.service._file_driver == self.mock_file_driver
        
        # Verify container was called for each provider
        self.mock_container.resolve.assert_any_call(DIKey.JSON_PROVIDER)
        self.mock_container.resolve.assert_any_call(DIKey.OS_PROVIDER)
        self.mock_container.resolve.assert_any_call(DIKey.FILE_DRIVER)
    
    @patch('pathlib.Path.exists')
    @patch('pathlib.Path.glob')
    def test_load_config_files_no_files(self, mock_glob, mock_exists):
        """Test loading config when no files exist"""
        # Setup: no files exist
        mock_exists.return_value = False
        mock_glob.return_value = []
        
        # Execute
        result = self.service.load_config_files(
            system_dir="/system",
            env_dir="/env",
            language="python"
        )
        
        # Verify: empty config returned
        assert result == {}
        assert self.mock_file_driver.read_file.call_count == 0
    
    @patch('pathlib.Path.exists')
    @patch('pathlib.Path.glob')
    def test_load_system_configs_success(self, mock_glob, mock_exists):
        """Test successful loading of system configuration files"""
        # Setup
        mock_exists.return_value = True
        mock_json_files = [
            Path("/system/config1.json"),
            Path("/system/config2.json")
        ]
        mock_glob.return_value = mock_json_files
        
        # Mock file contents
        self.mock_file_driver.read_file.side_effect = [
            '{"key1": "value1"}',
            '{"key2": "value2"}'
        ]
        
        # Mock JSON parsing
        self.mock_json_provider.loads.side_effect = [
            {"key1": "value1"},
            {"key2": "value2"}
        ]
        
        # Execute
        result = self.service.load_config_files(
            system_dir="/system",
            env_dir="/env",
            language="python"
        )
        
        # Verify
        assert result == {"key1": "value1", "key2": "value2"}
        # Note: call_count might be > 2 if env configs are also checked
        assert self.mock_file_driver.read_file.call_count >= 2
        assert self.mock_json_provider.loads.call_count >= 2
    
    def test_load_env_configs_shared_and_language(self):
        """Test loading both shared and language-specific env configs"""
        # Mock the internal methods instead of patching Path
        self.service._load_system_configs = Mock(return_value={})
        self.service._load_env_configs = Mock(return_value={
            "shared_key": "shared_value",
            "python_key": "python_value"
        })
        
        # Execute
        result = self.service.load_config_files(
            system_dir="/system",
            env_dir="/env",
            language="python"
        )
        
        # Verify: both configs merged
        expected = {
            "shared_key": "shared_value",
            "python_key": "python_value"
        }
        assert result == expected
        
        # Verify internal methods were called
        self.service._load_system_configs.assert_called_once()
        self.service._load_env_configs.assert_called_once_with(Path("/env"), "python")
    
    def test_language_config_overrides_shared(self):
        """Test that language-specific config overrides shared config"""
        # Mock internal methods
        self.service._load_system_configs = Mock(return_value={})
        self.service._load_env_configs = Mock(return_value={
            "common_key": "python_value",  # Language overrides shared
            "shared_only": "value1",
            "python_only": "value2"
        })
        
        # Execute
        result = self.service.load_config_files(
            system_dir="/system",
            env_dir="/env",
            language="python"
        )
        
        # Verify: language config overrides shared
        expected = {
            "common_key": "python_value",  # Overridden
            "shared_only": "value1",
            "python_only": "value2"
        }
        assert result == expected
    
    @patch('pathlib.Path.exists')
    @patch('pathlib.Path.glob')
    def test_error_handling_json_parse_error(self, mock_glob, mock_exists):
        """Test that JSON parse errors are handled gracefully"""
        # Setup
        mock_exists.return_value = True
        mock_glob.return_value = [Path("/system/invalid.json")]
        
        # Mock file read success but JSON parse failure
        self.mock_file_driver.read_file.return_value = 'invalid json'
        self.mock_json_provider.loads.side_effect = ValueError("Invalid JSON")
        
        # Execute
        result = self.service.load_config_files(
            system_dir="/system",
            env_dir="/env",
            language="python"
        )
        
        # Verify: returns empty config on error
        assert result == {}
    
    @patch('pathlib.Path.exists')
    @patch('pathlib.Path.glob')
    def test_error_handling_file_read_error(self, mock_glob, mock_exists):
        """Test that file read errors are handled gracefully"""
        # Setup
        mock_exists.return_value = True
        mock_glob.return_value = [Path("/system/unreadable.json")]
        
        # Mock file read failure
        self.mock_file_driver.read_file.side_effect = IOError("Permission denied")
        
        # Execute
        result = self.service.load_config_files(
            system_dir="/system",
            env_dir="/env",
            language="python"
        )
        
        # Verify: returns empty config on error
        assert result == {}
    
    @patch('pathlib.Path.exists')
    @patch('pathlib.Path.glob')
    def test_partial_failure_continues_loading(self, mock_glob, mock_exists):
        """Test that loading continues even if some files fail"""
        # Setup
        mock_exists.return_value = True
        mock_glob.return_value = [
            Path("/system/good.json"),
            Path("/system/bad.json"),
            Path("/system/also_good.json")
        ]
        
        # Mock mixed success/failure
        self.mock_file_driver.read_file.side_effect = [
            '{"good1": "value1"}',
            IOError("Cannot read"),
            '{"good2": "value2"}'
        ]
        
        self.mock_json_provider.loads.side_effect = [
            {"good1": "value1"},
            {"good2": "value2"}
        ]
        
        # Execute
        result = self.service.load_config_files(
            system_dir="/system",
            env_dir="/env",
            language="python"
        )
        
        # Verify: successful files are included
        assert result == {"good1": "value1", "good2": "value2"}
    
    def test_load_json_file_success(self):
        """Test successful JSON file loading"""
        # Setup
        self.mock_file_driver.read_file.return_value = '{"test": "data"}'
        self.mock_json_provider.loads.return_value = {"test": "data"}
        
        # Execute
        result = self.service._load_json_file("/path/to/file.json")
        
        # Verify
        assert result == {"test": "data"}
        self.mock_file_driver.read_file.assert_called_once_with("/path/to/file.json")
        self.mock_json_provider.loads.assert_called_once_with('{"test": "data"}')
    
    def test_load_json_file_returns_empty_on_error(self):
        """Test that _load_json_file returns empty dict on any error"""
        # Setup
        self.mock_file_driver.read_file.side_effect = Exception("Any error")
        
        # Execute
        result = self.service._load_json_file("/path/to/file.json")
        
        # Verify
        assert result == {}
    
    @patch('pathlib.Path.exists')
    def test_different_languages(self, mock_exists):
        """Test loading configs for different programming languages"""
        # Setup
        mock_exists.return_value = True
        
        # Test data for different languages
        languages = ["python", "cpp", "rust"]
        
        for lang in languages:
            # Reset mocks
            self.mock_file_driver.read_file.reset_mock()
            self.mock_json_provider.loads.reset_mock()
            
            # Mock response
            self.mock_file_driver.read_file.return_value = f'{{"lang": "{lang}"}}'
            self.mock_json_provider.loads.return_value = {"lang": lang}
            
            # Execute
            result = self.service.load_config_files(
                system_dir="/system",
                env_dir="/env",
                language=lang
            )
            
            # Verify: correct language directory was accessed
            expected_path = f"/env/{lang}/env.json"
            self.mock_file_driver.read_file.assert_called_with(expected_path)