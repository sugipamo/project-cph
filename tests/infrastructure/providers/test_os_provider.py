"""Tests for OS provider implementations."""
import os
import pytest
from unittest.mock import Mock, patch
from typing import List

from src.infrastructure.os_provider import SystemOsProvider, MockOsProvider, OsProvider


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


class TestMockOsProvider:
    """Tests for MockOsProvider."""
    
    def test_initialization(self):
        """Test MockOsProvider initialization."""
        provider = MockOsProvider()
        assert provider._current_dir == "/mock_cwd"
        assert provider._filesystem == {}
        assert provider._dir_contents == {}
    
    def test_file_operations(self):
        """Test file-related operations."""
        provider = MockOsProvider()
        
        # Test adding and checking files
        provider.add_file("/test/file.txt")
        assert provider.exists("/test/file.txt") is True
        assert provider.path_exists("/test/file.txt") is True
        assert provider.isfile("/test/file.txt") is True
        assert provider.path_isfile("/test/file.txt") is True
        assert provider.isdir("/test/file.txt") is False
        assert provider.path_isdir("/test/file.txt") is False
        
        # Test removing files
        provider.remove("/test/file.txt")
        assert provider.exists("/test/file.txt") is False
        
        # Test removing non-existent file
        with pytest.raises(FileNotFoundError, match="File /nonexistent not found"):
            provider.remove("/nonexistent")
    
    def test_directory_operations(self):
        """Test directory-related operations."""
        provider = MockOsProvider()
        
        # Test adding directories
        provider.add_directory("/test/dir", ["file1", "file2"])
        assert provider.exists("/test/dir") is True
        assert provider.isdir("/test/dir") is True
        assert provider.path_isdir("/test/dir") is True
        assert provider.isfile("/test/dir") is False
        
        # Test listing directory contents
        assert provider.listdir("/test/dir") == ["file1", "file2"]
        assert provider.listdir("/nonexistent") == []
        
        # Test makedirs
        provider.makedirs("/new/dir", exist_ok=True)
        assert provider.exists("/new/dir") is True
        assert provider.isdir("/new/dir") is True
        assert provider.listdir("/new/dir") == []
        
        # Test makedirs with exist_ok=False
        with pytest.raises(FileExistsError, match="Directory /new/dir already exists"):
            provider.makedirs("/new/dir", exist_ok=False)
        
        # Test rmdir
        provider.rmdir("/new/dir")
        assert provider.exists("/new/dir") is False
        
        # Test rmdir non-existent
        with pytest.raises(FileNotFoundError, match="Directory /nonexistent not found"):
            provider.rmdir("/nonexistent")
    
    def test_path_operations(self):
        """Test path manipulation methods."""
        provider = MockOsProvider()
        
        # Test path join
        assert provider.path_join("a", "b", "c") == "a/b/c"
        
        # Test dirname
        assert provider.path_dirname("/path/to/file.txt") == "/path/to"
        
        # Test dirname with no directory component
        with pytest.raises(ValueError, match="Path 'file.txt' has no directory component"):
            provider.path_dirname("file.txt")
        
        # Test basename
        assert provider.path_basename("/path/to/file.txt") == "file.txt"
        assert provider.path_basename("file.txt") == "file.txt"
    
    def test_working_directory_operations(self):
        """Test current working directory operations."""
        provider = MockOsProvider()
        
        # Test initial directory
        assert provider.getcwd() == "/mock_cwd"
        
        # Test changing directory
        provider.chdir("/new/dir")
        assert provider.getcwd() == "/new/dir"
    
    def test_non_existent_paths(self):
        """Test operations on non-existent paths."""
        provider = MockOsProvider()
        
        # Test checking non-existent paths
        assert provider.exists("/nonexistent") is False
        assert provider.path_exists("/nonexistent") is False
        assert provider.isdir("/nonexistent") is False
        assert provider.path_isdir("/nonexistent") is False
        assert provider.isfile("/nonexistent") is False
        assert provider.path_isfile("/nonexistent") is False
    
    def test_add_directory_requires_contents(self):
        """Test that add_directory requires explicit contents."""
        provider = MockOsProvider()
        
        # Test with None contents
        with pytest.raises(ValueError, match="Contents must be explicitly provided"):
            provider.add_directory("/test/dir", None)
        
        # Test with empty list (valid)
        provider.add_directory("/test/empty", [])
        assert provider.listdir("/test/empty") == []


class TestOsProviderAbstraction:
    """Test the abstract interface."""
    
    def test_abstract_methods(self):
        """Test that OsProvider is abstract and cannot be instantiated."""
        with pytest.raises(TypeError):
            OsProvider()
    
    def test_all_methods_implemented(self):
        """Test that concrete providers implement all abstract methods."""
        # Get all abstract methods from OsProvider
        abstract_methods = {
            name for name, method in vars(OsProvider).items()
            if hasattr(method, '__isabstractmethod__') and method.__isabstractmethod__
        }
        
        # Check SystemOsProvider
        for method_name in abstract_methods:
            assert hasattr(SystemOsProvider, method_name)
            assert callable(getattr(SystemOsProvider, method_name))
        
        # Check MockOsProvider
        for method_name in abstract_methods:
            assert hasattr(MockOsProvider, method_name)
            assert callable(getattr(MockOsProvider, method_name))