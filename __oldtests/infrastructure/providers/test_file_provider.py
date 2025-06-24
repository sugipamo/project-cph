"""Tests for file provider implementations."""
import tempfile
from pathlib import Path

import pytest

from src.infrastructure.providers.file_provider import MockFileProvider, SystemFileProvider


class TestSystemFileProvider:
    """Test SystemFileProvider functionality."""

    @pytest.fixture
    def file_provider(self):
        """Create SystemFileProvider instance."""
        return SystemFileProvider()

    @pytest.fixture
    def temp_file(self):
        """Create a temporary file for testing."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
            f.write("test content")
            temp_path = f.name
        yield temp_path
        Path(temp_path).unlink(missing_ok=True)

    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for testing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create some test files
            test_file1 = Path(temp_dir) / "file1.txt"
            test_file1.write_text("content1")
            test_file2 = Path(temp_dir) / "file2.txt"
            test_file2.write_text("content2")
            yield temp_dir

    def test_read_text_file_success(self, file_provider, temp_file):
        """Test reading existing text file."""
        content = file_provider.read_text_file(temp_file)
        assert content == "test content"

    def test_read_text_file_with_encoding(self, file_provider):
        """Test reading text file with specified encoding."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, encoding='utf-8') as f:
            f.write("テスト内容")
            temp_path = f.name

        try:
            content = file_provider.read_text_file(temp_path, encoding='utf-8')
            assert content == "テスト内容"
        finally:
            Path(temp_path).unlink(missing_ok=True)


    def test_write_text_file_success(self, file_provider):
        """Test writing text file."""
        with tempfile.NamedTemporaryFile(delete=False) as f:
            temp_path = f.name

        try:
            file_provider.write_text_file(temp_path, "new content")

            # Verify content was written
            with open(temp_path) as f:
                assert f.read() == "new content"
        finally:
            Path(temp_path).unlink(missing_ok=True)

    def test_write_text_file_with_encoding(self, file_provider):
        """Test writing text file with specified encoding."""
        with tempfile.NamedTemporaryFile(delete=False) as f:
            temp_path = f.name

        try:
            file_provider.write_text_file(temp_path, "テスト内容", encoding='utf-8')

            # Verify content was written with correct encoding
            with open(temp_path, encoding='utf-8') as f:
                assert f.read() == "テスト内容"
        finally:
            Path(temp_path).unlink(missing_ok=True)

    def test_file_exists_true(self, file_provider, temp_file):
        """Test file_exists returns True for existing file."""
        assert file_provider.file_exists(temp_file) is True

    def test_file_exists_false(self, file_provider):
        """Test file_exists returns False for non-existent file."""
        assert file_provider.file_exists("/nonexistent/file.txt") is False

    def test_list_directory_success(self, file_provider, temp_dir):
        """Test listing directory contents."""
        files = file_provider.list_directory(temp_dir)
        assert len(files) == 2
        assert "file1.txt" in files
        assert "file2.txt" in files

    def test_list_directory_empty(self, file_provider):
        """Test listing empty directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            files = file_provider.list_directory(temp_dir)
            assert files == []

    def test_list_directory_not_exists(self, file_provider):
        """Test listing non-existent directory returns empty list."""
        files = file_provider.list_directory("/nonexistent/directory")
        assert files == []

    def test_list_directory_not_a_directory(self, file_provider, temp_file):
        """Test listing a file (not directory) returns empty list."""
        files = file_provider.list_directory(temp_file)
        assert files == []


class TestMockFileProvider:
    """Test MockFileProvider functionality."""

    @pytest.fixture
    def mock_provider(self):
        """Create MockFileProvider instance."""
        return MockFileProvider()

    def test_add_file_and_read(self, mock_provider):
        """Test adding file and reading it back."""
        mock_provider.add_file("test.txt", "test content")
        content = mock_provider.read_text_file("test.txt")
        assert content == "test content"


    def test_write_text_file(self, mock_provider):
        """Test writing text file."""
        mock_provider.write_text_file("new.txt", "new content")
        content = mock_provider.read_text_file("new.txt")
        assert content == "new content"

    def test_write_text_file_overwrites(self, mock_provider):
        """Test writing overwrites existing file."""
        mock_provider.add_file("test.txt", "original")
        mock_provider.write_text_file("test.txt", "overwritten")
        content = mock_provider.read_text_file("test.txt")
        assert content == "overwritten"

    def test_file_exists_true(self, mock_provider):
        """Test file_exists returns True for existing file."""
        mock_provider.add_file("exists.txt", "content")
        assert mock_provider.file_exists("exists.txt") is True

    def test_file_exists_false(self, mock_provider):
        """Test file_exists returns False for non-existent file."""
        assert mock_provider.file_exists("notexists.txt") is False

    def test_list_directory_with_files(self, mock_provider):
        """Test listing directory with files."""
        mock_provider.add_file("dir/file1.txt", "content1")
        mock_provider.add_file("dir/file2.txt", "content2")
        mock_provider.add_file("dir/subdir/file3.txt", "content3")
        mock_provider.add_file("other/file4.txt", "content4")

        files = mock_provider.list_directory("dir")
        assert len(files) == 2
        assert "file1.txt" in files
        assert "file2.txt" in files
        assert "subdir" not in files  # Subdirectories should not be included

    def test_list_directory_empty(self, mock_provider):
        """Test listing empty directory."""
        files = mock_provider.list_directory("empty")
        assert files == []

    def test_list_directory_with_trailing_slash(self, mock_provider):
        """Test listing directory with trailing slash."""
        mock_provider.add_file("dir/file1.txt", "content1")
        mock_provider.add_file("dir/file2.txt", "content2")

        files = mock_provider.list_directory("dir/")
        assert len(files) == 2
        assert "file1.txt" in files
        assert "file2.txt" in files

    def test_encoding_parameter_ignored(self, mock_provider):
        """Test that encoding parameter is accepted but ignored in mock."""
        mock_provider.write_text_file("test.txt", "content", encoding="utf-8")
        content = mock_provider.read_text_file("test.txt", encoding="utf-8")
        assert content == "content"
