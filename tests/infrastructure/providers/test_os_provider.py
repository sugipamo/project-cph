"""Tests for OS provider implementations."""
import os
import pytest
from unittest.mock import Mock, patch
from typing import List

from src.infrastructure.os_provider import SystemOsProvider


class TestSystemOsProvider:
    """Tests for SystemOsProvider."""
    
    def test_path_operations(self):
        """Test path manipulation methods."""
        provider = SystemOsProvider()
        
        # Test path join
        assert provider.path_join("a", "b", "c") == os.path.join("a", "b", "c")
        
        # Test dirname
        assert provider.path_dirname("/path/to/file.txt") == "/path/to"
        
        # Test basename
        assert provider.path_basename("/path/to/file.txt") == "file.txt"
    
    def test_exists_checks(self):
        """Test various existence check methods."""
        provider = SystemOsProvider()
        
        with patch('os.path.exists', return_value=True):
            assert provider.exists("/some/path") is True
            assert provider.path_exists("/some/path") is True
        
        with patch('os.path.exists', return_value=False):
            assert provider.exists("/nonexistent") is False
            assert provider.path_exists("/nonexistent") is False
    
    def test_directory_operations(self):
        """Test directory-related operations."""
        provider = SystemOsProvider()
        
        # Test isdir
        with patch('os.path.isdir', return_value=True):
            assert provider.isdir("/some/dir") is True
            assert provider.path_isdir("/some/dir") is True
        
        # Test makedirs
        with patch('os.makedirs') as mock_makedirs:
            provider.makedirs("/new/dir", exist_ok=True)
            mock_makedirs.assert_called_once_with("/new/dir", exist_ok=True)
        
        # Test rmdir
        with patch('os.rmdir') as mock_rmdir:
            provider.rmdir("/empty/dir")
            mock_rmdir.assert_called_once_with("/empty/dir")
        
        # Test listdir
        with patch('os.listdir', return_value=["file1", "file2", "dir1"]):
            result = provider.listdir("/some/path")
            assert result == ["file1", "file2", "dir1"]
    
    def test_file_operations(self):
        """Test file-related operations."""
        provider = SystemOsProvider()
        
        # Test isfile
        with patch('os.path.isfile', return_value=True):
            assert provider.isfile("/some/file.txt") is True
            assert provider.path_isfile("/some/file.txt") is True
        
        # Test remove
        with patch('os.remove') as mock_remove:
            provider.remove("/file/to/delete.txt")
            mock_remove.assert_called_once_with("/file/to/delete.txt")
    
    def test_working_directory_operations(self):
        """Test current working directory operations."""
        provider = SystemOsProvider()
        
        # Test getcwd
        with patch('os.getcwd', return_value="/current/dir"):
            assert provider.getcwd() == "/current/dir"
        
        # Test chdir
        with patch('os.chdir') as mock_chdir:
            provider.chdir("/new/working/dir")
            mock_chdir.assert_called_once_with("/new/working/dir")
    
    def test_error_handling(self):
        """Test that errors are properly propagated."""
        provider = SystemOsProvider()
        
        # Test OSError propagation
        with patch('os.listdir', side_effect=OSError("Permission denied")):
            with pytest.raises(OSError, match="Permission denied"):
                provider.listdir("/restricted")
        
        # Test FileNotFoundError
        with patch('os.remove', side_effect=FileNotFoundError("No such file")):
            with pytest.raises(FileNotFoundError, match="No such file"):
                provider.remove("/nonexistent.txt")