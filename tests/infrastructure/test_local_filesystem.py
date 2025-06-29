"""Tests for LocalFileSystem implementation."""
import pytest
from pathlib import Path
from unittest.mock import Mock, MagicMock
from src.infrastructure.local_filesystem import LocalFileSystem, FileSystemError


class TestLocalFileSystem:
    """Test cases for LocalFileSystem."""

    def test_init_with_config_provider(self):
        """Test initialization with config provider."""
        mock_config_provider = Mock()
        fs = LocalFileSystem(mock_config_provider)
        assert fs.config_provider == mock_config_provider

    def test_init_with_none_config_provider(self):
        """Test initialization with None config provider."""
        fs = LocalFileSystem(None)
        assert fs.config_provider is None

    def test_exists_returns_true_for_existing_path(self):
        """Test exists returns True for existing path."""
        fs = LocalFileSystem(None)
        mock_path = Mock(spec=Path)
        mock_path.exists.return_value = True
        
        result = fs.exists(mock_path)
        
        assert result is True
        mock_path.exists.assert_called_once()

    def test_exists_returns_false_for_non_existing_path(self):
        """Test exists returns False for non-existing path."""
        fs = LocalFileSystem(None)
        mock_path = Mock(spec=Path)
        mock_path.exists.return_value = False
        
        result = fs.exists(mock_path)
        
        assert result is False
        mock_path.exists.assert_called_once()

    def test_is_file_returns_true_for_file(self):
        """Test is_file returns True for file path."""
        fs = LocalFileSystem(None)
        mock_path = Mock(spec=Path)
        mock_path.is_file.return_value = True
        
        result = fs.is_file(mock_path)
        
        assert result is True
        mock_path.is_file.assert_called_once()

    def test_is_file_returns_false_for_non_file(self):
        """Test is_file returns False for non-file path."""
        fs = LocalFileSystem(None)
        mock_path = Mock(spec=Path)
        mock_path.is_file.return_value = False
        
        result = fs.is_file(mock_path)
        
        assert result is False
        mock_path.is_file.assert_called_once()

    def test_is_dir_returns_true_for_directory(self):
        """Test is_dir returns True for directory path."""
        fs = LocalFileSystem(None)
        mock_path = Mock(spec=Path)
        mock_path.is_dir.return_value = True
        
        result = fs.is_dir(mock_path)
        
        assert result is True
        mock_path.is_dir.assert_called_once()

    def test_is_dir_returns_false_for_non_directory(self):
        """Test is_dir returns False for non-directory path."""
        fs = LocalFileSystem(None)
        mock_path = Mock(spec=Path)
        mock_path.is_dir.return_value = False
        
        result = fs.is_dir(mock_path)
        
        assert result is False
        mock_path.is_dir.assert_called_once()

    def test_iterdir_success(self):
        """Test iterdir returns list of paths."""
        fs = LocalFileSystem(None)
        mock_path = Mock(spec=Path)
        mock_file1 = Mock(spec=Path)
        mock_file2 = Mock(spec=Path)
        mock_path.iterdir.return_value = [mock_file1, mock_file2]
        
        result = fs.iterdir(mock_path)
        
        assert result == [mock_file1, mock_file2]
        mock_path.iterdir.assert_called_once()

    def test_iterdir_os_error_without_config_provider(self):
        """Test iterdir raises FileSystemError on OSError without config provider."""
        fs = LocalFileSystem(None)
        mock_path = Mock(spec=Path)
        mock_path.iterdir.side_effect = OSError("Permission denied")
        
        with pytest.raises(FileSystemError) as exc_info:
            fs.iterdir(mock_path)
        
        assert "Failed to list directory contents" in str(exc_info.value)
        assert "Permission denied" in str(exc_info.value)

    def test_iterdir_permission_error_with_config_provider_error_action(self):
        """Test iterdir with config provider and error action."""
        mock_config_provider = Mock()
        mock_config_provider.resolve_config.return_value = 'error'
        fs = LocalFileSystem(mock_config_provider)
        
        mock_path = Mock(spec=Path)
        mock_path.iterdir.side_effect = PermissionError("Access denied")
        
        with pytest.raises(FileSystemError) as exc_info:
            fs.iterdir(mock_path)
        
        assert "Failed to list directory contents" in str(exc_info.value)
        assert "Access denied" in str(exc_info.value)
        mock_config_provider.resolve_config.assert_called_once_with(
            ['filesystem_config', 'error_handling', 'permission_denied_action'],
            str
        )

    def test_iterdir_permission_error_with_invalid_error_action(self):
        """Test iterdir with invalid error action configuration."""
        mock_config_provider = Mock()
        mock_config_provider.resolve_config.return_value = 'invalid_action'
        fs = LocalFileSystem(mock_config_provider)
        
        mock_path = Mock(spec=Path)
        mock_path.iterdir.side_effect = PermissionError("Access denied")
        
        with pytest.raises(FileSystemError) as exc_info:
            fs.iterdir(mock_path)
        
        assert "Invalid error action configured: invalid_action" in str(exc_info.value)
        assert "Must be 'error'" in str(exc_info.value)

    def test_mkdir_creates_directory(self):
        """Test mkdir creates directory."""
        fs = LocalFileSystem(None)
        mock_path = Mock(spec=Path)
        
        fs.mkdir(mock_path, parents=True, exist_ok=True)
        
        mock_path.mkdir.assert_called_once_with(parents=True, exist_ok=True)

    def test_mkdir_without_parents_and_exist_ok(self):
        """Test mkdir without parents and exist_ok flags."""
        fs = LocalFileSystem(None)
        mock_path = Mock(spec=Path)
        
        fs.mkdir(mock_path, parents=False, exist_ok=False)
        
        mock_path.mkdir.assert_called_once_with(parents=False, exist_ok=False)

    def test_delete_file_not_implemented(self):
        """Test delete_file raises NotImplementedError."""
        fs = LocalFileSystem(None)
        mock_path = Mock(spec=Path)
        
        with pytest.raises(NotImplementedError) as exc_info:
            fs.delete_file(mock_path)
        
        assert "delete_file is not implemented" in str(exc_info.value)

    def test_create_directory_not_implemented(self):
        """Test create_directory raises NotImplementedError."""
        fs = LocalFileSystem(None)
        mock_path = Mock(spec=Path)
        
        with pytest.raises(NotImplementedError) as exc_info:
            fs.create_directory(mock_path)
        
        assert "create_directory is not implemented" in str(exc_info.value)