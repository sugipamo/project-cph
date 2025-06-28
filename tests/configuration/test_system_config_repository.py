import pytest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
import json

from src.configuration.system_config_repository import SystemConfigRepository


class TestSystemConfigRepository:
    @pytest.fixture
    def mock_json_provider(self):
        return Mock()

    @pytest.fixture
    def mock_file_driver(self):
        return Mock()

    @pytest.fixture
    def repository(self, mock_json_provider, mock_file_driver):
        return SystemConfigRepository(mock_json_provider, mock_file_driver)

    def test_init(self, mock_json_provider, mock_file_driver):
        repo = SystemConfigRepository(mock_json_provider, mock_file_driver)
        assert repo._json_provider == mock_json_provider
        assert repo._file_driver == mock_file_driver

    def test_load_system_configs_success(self, repository, mock_json_provider, mock_file_driver):
        config_dir = Path("/test/config")
        
        # Mock glob to return config files
        mock_file_driver.glob.return_value = [
            Path("/test/config/config1.json"),
            Path("/test/config/config2.json"),
        ]
        
        # Mock json loading
        mock_json_provider.load.side_effect = [
            {"key1": "value1"},
            {"key2": "value2"},
        ]
        
        result = repository.load_system_configs(config_dir)
        
        assert result == {
            "config1": {"key1": "value1"},
            "config2": {"key2": "value2"},
        }
        
        mock_file_driver.glob.assert_called_once_with(config_dir, "*.json")
        assert mock_json_provider.load.call_count == 2

    def test_load_system_configs_with_error(self, repository, mock_json_provider, mock_file_driver):
        config_dir = Path("/test/config")
        
        mock_file_driver.glob.return_value = [
            Path("/test/config/config1.json"),
            Path("/test/config/bad.json"),
        ]
        
        # First file loads fine, second fails
        mock_json_provider.load.side_effect = [
            {"key1": "value1"},
            Exception("JSON parse error"),
        ]
        
        result = repository.load_system_configs(config_dir)
        
        # Should still return the successful load
        assert result == {"config1": {"key1": "value1"}}

    def test_load_env_configs_single_language(self, repository, mock_json_provider, mock_file_driver):
        env_dir = Path("/test/env")
        language = "python"
        
        # Mock directory existence checks
        mock_file_driver.exists.side_effect = lambda p: p == env_dir / language
        
        # Mock glob results
        def mock_glob(path, pattern):
            if path == env_dir / "shared":
                return []
            elif path == env_dir / language:
                return [Path(f"/test/env/{language}/config.json")]
            return []
        
        mock_file_driver.glob.side_effect = mock_glob
        
        mock_json_provider.load.return_value = {"lang_key": "lang_value"}
        
        result = repository.load_env_configs(env_dir, language)
        
        assert result == {"config": {"lang_key": "lang_value"}}

    def test_load_env_configs_with_shared(self, repository, mock_json_provider, mock_file_driver):
        env_dir = Path("/test/env")
        language = "python"
        
        # Mock directory existence
        mock_file_driver.exists.return_value = True
        
        # Mock glob results
        def mock_glob(path, pattern):
            if path == env_dir / "shared":
                return [Path("/test/env/shared/common.json")]
            elif path == env_dir / language:
                return [Path(f"/test/env/{language}/config.json")]
            return []
        
        mock_file_driver.glob.side_effect = mock_glob
        
        # Mock json loads
        mock_json_provider.load.side_effect = [
            {"shared_key": "shared_value"},
            {"lang_key": "lang_value"},
        ]
        
        result = repository.load_env_configs(env_dir, language)
        
        assert result == {
            "common": {"shared_key": "shared_value"},
            "config": {"lang_key": "lang_value"},
        }

    def test_save_config(self, repository, mock_json_provider, mock_file_driver):
        config_path = Path("/test/config.json")
        config_data = {"key": "value"}
        
        repository.save_config(config_path, config_data)
        
        mock_json_provider.save.assert_called_once_with(config_path, config_data)

    def test_load_config_success(self, repository, mock_json_provider, mock_file_driver):
        config_path = Path("/test/config.json")
        
        mock_file_driver.exists.return_value = True
        mock_json_provider.load.return_value = {"key": "value"}
        
        result = repository.load_config(config_path)
        
        assert result == {"key": "value"}
        mock_file_driver.exists.assert_called_once_with(config_path)
        mock_json_provider.load.assert_called_once_with(config_path)

    def test_load_config_not_found(self, repository, mock_json_provider, mock_file_driver):
        config_path = Path("/test/config.json")
        
        mock_file_driver.exists.return_value = False
        
        result = repository.load_config(config_path)
        
        assert result is None
        mock_file_driver.exists.assert_called_once_with(config_path)
        mock_json_provider.load.assert_not_called()

    def test_load_config_with_error(self, repository, mock_json_provider, mock_file_driver):
        config_path = Path("/test/config.json")
        
        mock_file_driver.exists.return_value = True
        mock_json_provider.load.side_effect = Exception("Parse error")
        
        result = repository.load_config(config_path)
        
        assert result is None

    def test_ensure_config_dir(self, repository, mock_file_driver):
        config_dir = Path("/test/config")
        
        repository.ensure_config_dir(config_dir)
        
        mock_file_driver.mkdir.assert_called_once_with(config_dir, parents=True, exist_ok=True)

    def test_list_configs(self, repository, mock_file_driver):
        config_dir = Path("/test/config")
        
        mock_file_driver.glob.return_value = [
            Path("/test/config/a.json"),
            Path("/test/config/b.json"),
        ]
        
        result = repository.list_configs(config_dir)
        
        assert result == ["a", "b"]
        mock_file_driver.glob.assert_called_once_with(config_dir, "*.json")

    def test_delete_config(self, repository, mock_file_driver):
        config_path = Path("/test/config.json")
        
        mock_file_driver.exists.return_value = True
        
        result = repository.delete_config(config_path)
        
        assert result is True
        mock_file_driver.unlink.assert_called_once_with(config_path)

    def test_delete_config_not_found(self, repository, mock_file_driver):
        config_path = Path("/test/config.json")
        
        mock_file_driver.exists.return_value = False
        
        result = repository.delete_config(config_path)
        
        assert result is False
        mock_file_driver.unlink.assert_not_called()

    def test_copy_config(self, repository, mock_file_driver):
        source = Path("/test/source.json")
        dest = Path("/test/dest.json")
        
        mock_file_driver.exists.return_value = True
        
        result = repository.copy_config(source, dest)
        
        assert result is True
        mock_file_driver.copy.assert_called_once_with(source, dest)

    def test_copy_config_source_not_found(self, repository, mock_file_driver):
        source = Path("/test/source.json")
        dest = Path("/test/dest.json")
        
        mock_file_driver.exists.return_value = False
        
        result = repository.copy_config(source, dest)
        
        assert result is False
        mock_file_driver.copy.assert_not_called()