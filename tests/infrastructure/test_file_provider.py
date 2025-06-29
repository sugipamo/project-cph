"""Tests for file provider implementations"""
import pytest
from pathlib import Path
import tempfile
import os
from src.infrastructure.file_provider import FileProvider, SystemFileProvider, MockFileProvider


class TestSystemFileProvider:
    """Test cases for SystemFileProvider"""

    @pytest.fixture
    def provider(self):
        """Create SystemFileProvider instance"""
        return SystemFileProvider()

    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for tests"""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield tmpdir

    def test_read_text_file_success(self, provider, temp_dir):
        """Test successful file reading"""
        # Create test file
        test_file = os.path.join(temp_dir, "test.txt")
        content = "Hello, World!\nこんにちは"
        with open(test_file, 'w', encoding='utf-8') as f:
            f.write(content)
        
        # Test reading
        result = provider.read_text_file(test_file, 'utf-8')
        assert result == content

    def test_read_text_file_not_found(self, provider, temp_dir):
        """Test reading non-existent file"""
        non_existent = os.path.join(temp_dir, "does_not_exist.txt")
        
        with pytest.raises(FileNotFoundError):
            provider.read_text_file(non_existent, 'utf-8')

    def test_write_text_file_success(self, provider, temp_dir):
        """Test successful file writing"""
        test_file = os.path.join(temp_dir, "output.txt")
        content = "Test content\nLine 2"
        
        provider.write_text_file(test_file, content, 'utf-8')
        
        # Verify file was written
        with open(test_file, 'r', encoding='utf-8') as f:
            assert f.read() == content

    def test_write_text_file_overwrite(self, provider, temp_dir):
        """Test overwriting existing file"""
        test_file = os.path.join(temp_dir, "existing.txt")
        
        # Write initial content
        provider.write_text_file(test_file, "Original", 'utf-8')
        
        # Overwrite
        new_content = "Updated content"
        provider.write_text_file(test_file, new_content, 'utf-8')
        
        # Verify new content
        with open(test_file, 'r', encoding='utf-8') as f:
            assert f.read() == new_content

    def test_file_exists_true(self, provider, temp_dir):
        """Test file_exists returns True for existing file"""
        test_file = os.path.join(temp_dir, "exists.txt")
        Path(test_file).touch()
        
        assert provider.file_exists(test_file) is True

    def test_file_exists_false(self, provider, temp_dir):
        """Test file_exists returns False for non-existent file"""
        non_existent = os.path.join(temp_dir, "not_there.txt")
        
        assert provider.file_exists(non_existent) is False

    def test_list_directory_success(self, provider, temp_dir):
        """Test listing directory contents"""
        # Create test files
        files = ["file1.txt", "file2.py", "data.json"]
        for filename in files:
            Path(os.path.join(temp_dir, filename)).touch()
        
        # Create subdirectory (should be included)
        subdir = os.path.join(temp_dir, "subdir")
        os.makedirs(subdir)
        
        result = provider.list_directory(temp_dir)
        
        # Check all files and directory are listed
        assert sorted(result) == sorted(files + ["subdir"])

    def test_list_directory_empty(self, provider, temp_dir):
        """Test listing empty directory"""
        empty_dir = os.path.join(temp_dir, "empty")
        os.makedirs(empty_dir)
        
        result = provider.list_directory(empty_dir)
        assert result == []

    def test_list_directory_non_existent(self, provider, temp_dir):
        """Test listing non-existent directory"""
        non_existent = os.path.join(temp_dir, "not_there")
        
        result = provider.list_directory(non_existent)
        assert result == []

    def test_list_directory_file_not_dir(self, provider, temp_dir):
        """Test listing when path is file, not directory"""
        file_path = os.path.join(temp_dir, "file.txt")
        Path(file_path).touch()
        
        result = provider.list_directory(file_path)
        assert result == []

    def test_list_directory_permission_error(self, provider, temp_dir, monkeypatch):
        """Test handling permission errors"""
        def mock_iterdir(self):
            raise PermissionError("Access denied")
        
        monkeypatch.setattr(Path, "iterdir", mock_iterdir)
        
        with pytest.raises(RuntimeError) as exc_info:
            provider.list_directory(temp_dir)
        
        assert "Failed to list directory" in str(exc_info.value)
        assert "Access denied" in str(exc_info.value)


class TestMockFileProvider:
    """Test cases for MockFileProvider"""

    @pytest.fixture
    def provider(self):
        """Create MockFileProvider instance"""
        return MockFileProvider()

    def test_read_text_file_success(self, provider):
        """Test reading file from mock"""
        provider.add_file("/test/file.txt", "Mock content")
        
        result = provider.read_text_file("/test/file.txt", 'utf-8')
        assert result == "Mock content"

    def test_read_text_file_not_found(self, provider):
        """Test reading non-existent file from mock"""
        with pytest.raises(FileNotFoundError) as exc_info:
            provider.read_text_file("/not/exists.txt", 'utf-8')
        
        assert "File not found: /not/exists.txt" in str(exc_info.value)

    def test_write_text_file(self, provider):
        """Test writing file to mock"""
        provider.write_text_file("/output/data.txt", "New content", 'utf-8')
        
        # Verify file was "written"
        assert provider.file_exists("/output/data.txt")
        assert provider.read_text_file("/output/data.txt", 'utf-8') == "New content"

    def test_file_exists(self, provider):
        """Test file existence check in mock"""
        provider.add_file("/exists.txt", "content")
        
        assert provider.file_exists("/exists.txt") is True
        assert provider.file_exists("/not_there.txt") is False

    def test_list_directory_root(self, provider):
        """Test listing mock directory at root"""
        # Add files in root
        provider.add_file("/file1.txt", "content1")
        provider.add_file("/file2.py", "content2")
        provider.add_file("/subdir/nested.txt", "nested")
        
        result = provider.list_directory("/")
        assert sorted(result) == ["file1.txt", "file2.py"]

    def test_list_directory_subdirectory(self, provider):
        """Test listing mock subdirectory"""
        # Add files in various locations
        provider.add_file("/root.txt", "root")
        provider.add_file("/test/file1.txt", "content1")
        provider.add_file("/test/file2.txt", "content2")
        provider.add_file("/test/sub/nested.txt", "nested")
        provider.add_file("/other/file.txt", "other")
        
        result = provider.list_directory("/test")
        assert sorted(result) == ["file1.txt", "file2.txt"]

    def test_list_directory_trailing_slash(self, provider):
        """Test listing directory handles trailing slash"""
        provider.add_file("/dir/file.txt", "content")
        
        # Both with and without trailing slash should work
        assert provider.list_directory("/dir") == ["file.txt"]
        assert provider.list_directory("/dir/") == ["file.txt"]

    def test_list_directory_empty(self, provider):
        """Test listing empty mock directory"""
        # Add file in different directory
        provider.add_file("/other/file.txt", "content")
        
        result = provider.list_directory("/empty")
        assert result == []

    def test_add_file_and_overwrite(self, provider):
        """Test adding and overwriting files in mock"""
        provider.add_file("/test.txt", "original")
        assert provider.read_text_file("/test.txt", 'utf-8') == "original"
        
        # Overwrite via write_text_file
        provider.write_text_file("/test.txt", "updated", 'utf-8')
        assert provider.read_text_file("/test.txt", 'utf-8') == "updated"
        
        # Overwrite via add_file
        provider.add_file("/test.txt", "final")
        assert provider.read_text_file("/test.txt", 'utf-8') == "final"

    def test_encoding_parameter_ignored_in_mock(self, provider):
        """Test that encoding parameter is accepted but not used in mock"""
        # Mock doesn't actually use encoding, but should accept it
        provider.write_text_file("/test.txt", "content", 'shift-jis')
        result = provider.read_text_file("/test.txt", 'ascii')
        assert result == "content"


class TestFileProviderInterface:
    """Test FileProvider ABC interface"""

    def test_cannot_instantiate_abstract_class(self):
        """Test that FileProvider cannot be instantiated directly"""
        with pytest.raises(TypeError):
            FileProvider()

    def test_concrete_classes_implement_interface(self):
        """Test that concrete classes implement all abstract methods"""
        # This test verifies that the classes can be instantiated
        system_provider = SystemFileProvider()
        mock_provider = MockFileProvider()
        
        # Verify they have all required methods
        for method in ['read_text_file', 'write_text_file', 'file_exists', 'list_directory']:
            assert hasattr(system_provider, method)
            assert hasattr(mock_provider, method)