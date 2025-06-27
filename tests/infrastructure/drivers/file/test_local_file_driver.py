"""Tests for LocalFileDriver - file system operations"""
import pytest
from pathlib import Path
from unittest.mock import Mock, patch, mock_open
import tempfile
import shutil
import os
from src.infrastructure.drivers.file.local_file_driver import LocalFileDriver


class TestLocalFileDriver:
    """Test suite for local file system driver"""
    
    def setup_method(self):
        """Set up test fixtures"""
        # Create a temporary directory for tests
        self.temp_dir = tempfile.mkdtemp()
        self.base_path = Path(self.temp_dir)
        self.driver = LocalFileDriver(base_dir=self.base_path)
    
    def teardown_method(self):
        """Clean up after tests"""
        # Remove temporary directory
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def test_resolve_path_absolute(self):
        """Test resolving absolute paths"""
        abs_path = Path("/absolute/path")
        resolved = self.driver.resolve_path(abs_path)
        assert resolved == abs_path
    
    def test_resolve_path_relative(self):
        """Test resolving relative paths"""
        rel_path = Path("relative/path")
        resolved = self.driver.resolve_path(rel_path)
        assert resolved == self.base_path / rel_path
    
    def test_exists_file(self):
        """Test checking if file exists"""
        # Create a test file
        test_file = self.base_path / "test.txt"
        test_file.write_text("test content")
        
        assert self.driver.exists(test_file) is True
        assert self.driver.exists(self.base_path / "nonexistent.txt") is False
    
    def test_exists_directory(self):
        """Test checking if directory exists"""
        # Create a test directory
        test_dir = self.base_path / "test_dir"
        test_dir.mkdir()
        
        assert self.driver.exists(test_dir) is True
        assert self.driver.exists(self.base_path / "nonexistent_dir") is False
    
    def test_isdir(self):
        """Test directory check"""
        # Create directory and file
        test_dir = self.base_path / "test_dir"
        test_dir.mkdir()
        test_file = self.base_path / "test.txt"
        test_file.write_text("content")
        
        assert self.driver.isdir(test_dir) is True
        assert self.driver.isdir(test_file) is False
        assert self.driver.isdir(self.base_path / "nonexistent") is False
    
    def test_is_file(self):
        """Test file check"""
        # Create file and directory
        test_file = self.base_path / "test.txt"
        test_file.write_text("content")
        test_dir = self.base_path / "test_dir"
        test_dir.mkdir()
        
        assert self.driver.is_file(test_file) is True
        assert self.driver.is_file(test_dir) is False
        assert self.driver.is_file(self.base_path / "nonexistent") is False
    
    def test_create_file(self):
        """Test file creation"""
        test_file = self.base_path / "new_file.txt"
        content = "Hello, World!"
        
        self.driver.create_file(test_file, content)
        
        assert test_file.exists()
        assert test_file.read_text() == content
    
    def test_create_file_with_parent_dirs(self):
        """Test file creation with parent directory creation"""
        test_file = self.base_path / "sub" / "dir" / "file.txt"
        content = "nested content"
        
        self.driver.create_file(test_file, content)
        
        assert test_file.exists()
        assert test_file.read_text() == content
    
    def test_copy_file(self):
        """Test file copy operation"""
        src_file = self.base_path / "source.txt"
        dst_file = self.base_path / "destination.txt"
        content = "copy me"
        
        src_file.write_text(content)
        self.driver.copy(src_file, dst_file)
        
        assert dst_file.exists()
        assert dst_file.read_text() == content
        assert src_file.exists()  # Original should still exist
    
    def test_move_file(self):
        """Test file move operation"""
        src_file = self.base_path / "source.txt"
        dst_file = self.base_path / "destination.txt"
        content = "move me"
        
        src_file.write_text(content)
        self.driver.move(src_file, dst_file)
        
        assert dst_file.exists()
        assert dst_file.read_text() == content
        assert not src_file.exists()  # Original should be gone
    
    def test_remove_file(self):
        """Test file removal"""
        test_file = self.base_path / "remove_me.txt"
        test_file.write_text("temporary")
        
        assert test_file.exists()
        self.driver.remove(test_file)
        assert not test_file.exists()
    
    def test_makedirs(self):
        """Test directory creation with parents"""
        test_dir = self.base_path / "level1" / "level2" / "level3"
        
        self.driver.makedirs(test_dir, exist_ok=True)
        
        assert test_dir.exists()
        assert test_dir.is_dir()
    
    def test_makedirs_exist_ok_false(self):
        """Test makedirs with exist_ok=False"""
        test_dir = self.base_path / "existing_dir"
        test_dir.mkdir()
        
        with pytest.raises(FileExistsError):
            self.driver.makedirs(test_dir, exist_ok=False)
    
    def test_mkdir_single_directory(self):
        """Test single directory creation"""
        test_dir = self.base_path / "single_dir"
        
        self.driver.mkdir(test_dir)
        
        assert test_dir.exists()
        assert test_dir.is_dir()
    
    def test_list_files(self):
        """Test listing files in directory (recursively)"""
        # Create test files
        (self.base_path / "file1.txt").write_text("1")
        (self.base_path / "file2.txt").write_text("2")
        (self.base_path / "subdir").mkdir()
        (self.base_path / "subdir" / "file3.txt").write_text("3")
        
        files = self.driver.list_files(self.base_path)
        
        # list_files is recursive and returns full paths
        assert any("file1.txt" in f for f in files)
        assert any("file2.txt" in f for f in files)
        assert any("file3.txt" in f for f in files)
        # Should not include directories, only files
        assert not any(f.endswith("subdir") for f in files)
        assert len(files) == 3
    
    def test_list_files_recursive(self):
        """Test recursive file listing"""
        # Create nested structure
        (self.base_path / "file1.txt").write_text("1")
        (self.base_path / "dir1").mkdir()
        (self.base_path / "dir1" / "file2.txt").write_text("2")
        (self.base_path / "dir1" / "dir2").mkdir()
        (self.base_path / "dir1" / "dir2" / "file3.txt").write_text("3")
        
        files = self.driver.list_files_recursive(self.base_path)
        file_paths = [str(f.relative_to(self.base_path)) for f in files]
        
        assert "file1.txt" in file_paths
        assert str(Path("dir1") / "file2.txt") in file_paths
        assert str(Path("dir1") / "dir2" / "file3.txt") in file_paths
    
    def test_copytree(self):
        """Test directory tree copy"""
        # Create source tree
        src_dir = self.base_path / "src_tree"
        src_dir.mkdir()
        (src_dir / "file1.txt").write_text("1")
        (src_dir / "subdir").mkdir()
        (src_dir / "subdir" / "file2.txt").write_text("2")
        
        dst_dir = self.base_path / "dst_tree"
        
        self.driver.copytree(src_dir, dst_dir)
        
        # Verify structure
        assert dst_dir.exists()
        assert (dst_dir / "file1.txt").read_text() == "1"
        assert (dst_dir / "subdir" / "file2.txt").read_text() == "2"
        assert src_dir.exists()  # Original should still exist
    
    def test_movetree(self):
        """Test directory tree move"""
        # Create source tree
        src_dir = self.base_path / "src_tree"
        src_dir.mkdir()
        (src_dir / "file1.txt").write_text("1")
        (src_dir / "subdir").mkdir()
        (src_dir / "subdir" / "file2.txt").write_text("2")
        
        dst_dir = self.base_path / "dst_tree"
        
        self.driver.movetree(src_dir, dst_dir)
        
        # Verify structure
        assert dst_dir.exists()
        assert (dst_dir / "file1.txt").read_text() == "1"
        assert (dst_dir / "subdir" / "file2.txt").read_text() == "2"
        assert not src_dir.exists()  # Original should be gone
    
    def test_rmtree(self):
        """Test directory tree removal"""
        # Create tree to remove
        test_dir = self.base_path / "remove_tree"
        test_dir.mkdir()
        (test_dir / "file1.txt").write_text("1")
        (test_dir / "subdir").mkdir()
        (test_dir / "subdir" / "file2.txt").write_text("2")
        
        assert test_dir.exists()
        self.driver.rmtree(test_dir)
        assert not test_dir.exists()
    
    def test_touch(self):
        """Test file touch operation"""
        test_file = self.base_path / "touch_me.txt"
        
        # Touch non-existent file
        self.driver.touch(test_file)
        assert test_file.exists()
        assert test_file.read_text() == ""
        
        # Touch existing file
        test_file.write_text("content")
        mtime_before = test_file.stat().st_mtime
        
        # Small delay to ensure timestamp difference
        import time
        time.sleep(0.01)
        
        self.driver.touch(test_file)
        mtime_after = test_file.stat().st_mtime
        
        assert test_file.read_text() == "content"  # Content preserved
        assert mtime_after > mtime_before  # Timestamp updated
    
    def test_glob_pattern(self):
        """Test glob pattern matching"""
        # Create test files
        (self.base_path / "test1.txt").write_text("1")
        (self.base_path / "test2.txt").write_text("2")
        (self.base_path / "other.py").write_text("3")
        (self.base_path / "subdir").mkdir()
        (self.base_path / "subdir" / "test3.txt").write_text("4")
        
        # Test simple pattern
        txt_files = self.driver.glob("*.txt")
        txt_names = [f.name for f in txt_files]
        
        assert "test1.txt" in txt_names
        assert "test2.txt" in txt_names
        assert "other.py" not in txt_names
        
        # Test recursive pattern
        all_txt = self.driver.glob("**/*.txt")
        all_txt_rel = [str(f.relative_to(self.base_path)) for f in all_txt]
        
        assert "test1.txt" in all_txt_rel
        assert "test2.txt" in all_txt_rel
        assert str(Path("subdir") / "test3.txt") in all_txt_rel
    
    def test_hash_file(self):
        """Test file hashing"""
        test_file = self.base_path / "hash_me.txt"
        content = "Hash this content"
        test_file.write_text(content)
        
        # Test MD5 hash
        md5_hash = self.driver.hash_file(test_file, "md5")
        assert len(md5_hash) == 32  # MD5 produces 32 hex characters
        
        # Test SHA256 hash
        sha256_hash = self.driver.hash_file(test_file, "sha256")
        assert len(sha256_hash) == 64  # SHA256 produces 64 hex characters
        
        # Same content should produce same hash
        test_file2 = self.base_path / "hash_me2.txt"
        test_file2.write_text(content)
        assert self.driver.hash_file(test_file2, "md5") == md5_hash
    
    def test_open_file(self):
        """Test file open operation"""
        test_file = self.base_path / "open_me.txt"
        
        # Write mode
        with self.driver.open(test_file, 'w', encoding='utf-8') as f:
            f.write("Hello, World!")
        
        assert test_file.read_text() == "Hello, World!"
        
        # Read mode
        with self.driver.open(test_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        assert content == "Hello, World!"
    
    def test_execute_command_interface(self):
        """Test execute_command interface method"""
        mock_request = Mock()
        
        # execute_command is implemented but does nothing (compatibility with BaseDriver)
        result = self.driver.execute_command(mock_request)
        # Should return None as the method is empty
        assert result is None
    
    def test_validate_interface(self):
        """Test validate interface method"""
        mock_request = Mock()
        
        # Should return True (file driver can handle file requests)
        assert self.driver.validate(mock_request) is True