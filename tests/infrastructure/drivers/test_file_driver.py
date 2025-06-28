"""Tests for File driver."""
import pytest
from unittest.mock import Mock, MagicMock, patch, mock_open
from pathlib import Path
import tempfile
import shutil
import os

from src.infrastructure.drivers.file.file_driver import FileDriver


class TestFileDriverInit:
    """Test File driver initialization."""

    def test_init_without_logger(self):
        """Test initialization without logger."""
        driver = FileDriver(logger=None)
        assert driver.logger is None

    def test_init_with_logger(self):
        """Test initialization with logger."""
        mock_logger = Mock()
        driver = FileDriver(logger=mock_logger)
        assert driver.logger == mock_logger


class TestFileDriverValidation:
    """Test File driver validation methods."""

    def setup_method(self):
        """Setup test driver."""
        self.driver = FileDriver(logger=None)

    def test_validate_valid_operations(self):
        """Test validation of valid operations."""
        valid_operations = [
            'read', 'write', 'copy', 'move', 'remove', 'mkdir', 'exists',
            'isdir', 'is_file', 'list_files', 'glob', 'hash'
        ]
        
        for op in valid_operations:
            request = Mock()
            request.operation = op
            assert self.driver.validate(request) is True

    def test_validate_invalid_operation(self):
        """Test validation of invalid operation."""
        request = Mock()
        request.operation = "invalid"
        assert self.driver.validate(request) is False

    def test_validate_no_operation_attribute(self):
        """Test validation when request has no operation attribute."""
        request = Mock(spec=[])
        assert self.driver.validate(request) is False


class TestFileDriverPathOperations:
    """Test path operations."""

    def setup_method(self):
        """Setup test driver."""
        self.driver = FileDriver(logger=None)

    def test_resolve_path_string(self):
        """Test resolving string path."""
        with patch('pathlib.Path.resolve') as mock_resolve:
            mock_resolve.return_value = Path('/absolute/path')
            result = self.driver.resolve_path('/some/path')
            assert result == Path('/absolute/path')

    def test_resolve_path_pathlib(self):
        """Test resolving Path object."""
        with patch('pathlib.Path.resolve') as mock_resolve:
            mock_resolve.return_value = Path('/absolute/path')
            result = self.driver.resolve_path(Path('/some/path'))
            assert result == Path('/absolute/path')

    def test_exists(self):
        """Test path existence check."""
        with patch.object(Path, 'exists') as mock_exists:
            mock_exists.return_value = True
            assert self.driver.exists('/some/path') is True
            
            mock_exists.return_value = False
            assert self.driver.exists('/some/path') is False

    def test_isdir(self):
        """Test directory check."""
        with patch.object(Path, 'is_dir') as mock_is_dir:
            mock_is_dir.return_value = True
            assert self.driver.isdir('/some/dir') is True
            
            mock_is_dir.return_value = False
            assert self.driver.isdir('/some/file') is False

    def test_is_file(self):
        """Test file check."""
        with patch.object(Path, 'is_file') as mock_is_file:
            mock_is_file.return_value = True
            assert self.driver.is_file('/some/file') is True
            
            mock_is_file.return_value = False
            assert self.driver.is_file('/some/dir') is False


class TestFileDriverFileOperations:
    """Test file operations."""

    def setup_method(self):
        """Setup test driver with temp directory."""
        self.driver = FileDriver(logger=None)
        self.temp_dir = tempfile.mkdtemp()

    def teardown_method(self):
        """Cleanup temp directory."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_create_file_simple(self):
        """Test creating a simple file."""
        file_path = Path(self.temp_dir) / "test.txt"
        self.driver.create_file(file_path, "Hello World")
        
        assert file_path.exists()
        assert file_path.read_text() == "Hello World"

    def test_create_file_with_parents(self):
        """Test creating file with parent directories."""
        file_path = Path(self.temp_dir) / "sub" / "dir" / "test.txt"
        self.driver.create_file(file_path, "Content", create_parents=True)
        
        assert file_path.exists()
        assert file_path.read_text() == "Content"

    def test_create_file_without_parents_fails(self):
        """Test creating file without parent directories fails."""
        file_path = Path(self.temp_dir) / "nonexistent" / "test.txt"
        
        with pytest.raises(FileNotFoundError):
            self.driver.create_file(file_path, "Content", create_parents=False)

    def test_read_file(self):
        """Test reading file content."""
        file_path = Path(self.temp_dir) / "test.txt"
        file_path.write_text("Test Content")
        
        content = self.driver.read_file(file_path)
        assert content == "Test Content"

    def test_read_file_not_exists(self):
        """Test reading non-existent file."""
        file_path = Path(self.temp_dir) / "nonexistent.txt"
        
        with pytest.raises(FileNotFoundError):
            self.driver.read_file(file_path)

    def test_copy_file(self):
        """Test copying a file."""
        source = Path(self.temp_dir) / "source.txt"
        dest = Path(self.temp_dir) / "dest.txt"
        source.write_text("Copy me")
        
        self.driver.copy(source, dest)
        
        assert dest.exists()
        assert dest.read_text() == "Copy me"
        assert source.exists()  # Original still exists

    def test_copy_directory(self):
        """Test copying a directory."""
        source_dir = Path(self.temp_dir) / "source_dir"
        source_dir.mkdir()
        (source_dir / "file.txt").write_text("Content")
        
        dest_dir = Path(self.temp_dir) / "dest_dir"
        
        self.driver.copy(source_dir, dest_dir)
        
        assert dest_dir.exists()
        assert (dest_dir / "file.txt").exists()
        assert (dest_dir / "file.txt").read_text() == "Content"

    def test_move_file(self):
        """Test moving a file."""
        source = Path(self.temp_dir) / "source.txt"
        dest = Path(self.temp_dir) / "dest.txt"
        source.write_text("Move me")
        
        self.driver.move(source, dest)
        
        assert dest.exists()
        assert dest.read_text() == "Move me"
        assert not source.exists()  # Original is gone

    def test_remove_file(self):
        """Test removing a file."""
        file_path = Path(self.temp_dir) / "remove_me.txt"
        file_path.write_text("Delete me")
        
        self.driver.remove(file_path)
        
        assert not file_path.exists()

    def test_remove_directory(self):
        """Test removing a directory."""
        dir_path = Path(self.temp_dir) / "remove_dir"
        dir_path.mkdir()
        (dir_path / "file.txt").write_text("Content")
        
        self.driver.remove(dir_path)
        
        assert not dir_path.exists()

    def test_touch(self):
        """Test touching a file."""
        file_path = Path(self.temp_dir) / "touch_me.txt"
        
        self.driver.touch(file_path)
        
        assert file_path.exists()
        assert file_path.read_text() == ""


class TestFileDriverDirectoryOperations:
    """Test directory operations."""

    def setup_method(self):
        """Setup test driver with temp directory."""
        self.driver = FileDriver(logger=None)
        self.temp_dir = tempfile.mkdtemp()

    def teardown_method(self):
        """Cleanup temp directory."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_mkdir(self):
        """Test creating a directory."""
        dir_path = Path(self.temp_dir) / "new_dir"
        
        self.driver.mkdir(dir_path, exist_ok=True)
        
        assert dir_path.exists()
        assert dir_path.is_dir()

    def test_mkdir_exist_ok(self):
        """Test creating existing directory with exist_ok."""
        dir_path = Path(self.temp_dir) / "existing_dir"
        dir_path.mkdir()
        
        # Should not raise error
        self.driver.mkdir(dir_path, exist_ok=True)

    def test_makedirs(self):
        """Test creating nested directories."""
        dir_path = Path(self.temp_dir) / "parent" / "child" / "grandchild"
        
        self.driver.makedirs(dir_path, exist_ok=True)
        
        assert dir_path.exists()
        assert dir_path.is_dir()

    def test_rmtree(self):
        """Test removing directory tree."""
        dir_path = Path(self.temp_dir) / "tree"
        sub_dir = dir_path / "sub"
        sub_dir.mkdir(parents=True)
        (sub_dir / "file.txt").write_text("Content")
        
        self.driver.rmtree(dir_path)
        
        assert not dir_path.exists()

    def test_list_files_non_recursive(self):
        """Test listing files non-recursively."""
        dir_path = Path(self.temp_dir) / "list_dir"
        dir_path.mkdir()
        (dir_path / "file1.txt").write_text("1")
        (dir_path / "file2.txt").write_text("2")
        sub_dir = dir_path / "sub"
        sub_dir.mkdir()
        (sub_dir / "file3.txt").write_text("3")
        
        files = self.driver.list_files(dir_path, recursive=False)
        
        assert len(files) == 2
        assert any(f.name == "file1.txt" for f in files)
        assert any(f.name == "file2.txt" for f in files)
        assert not any(f.name == "file3.txt" for f in files)

    def test_list_files_recursive(self):
        """Test listing files recursively."""
        dir_path = Path(self.temp_dir) / "list_dir"
        dir_path.mkdir()
        (dir_path / "file1.txt").write_text("1")
        sub_dir = dir_path / "sub"
        sub_dir.mkdir()
        (sub_dir / "file2.txt").write_text("2")
        
        files = self.driver.list_files(dir_path, recursive=True)
        
        assert len(files) == 2
        assert any(f.name == "file1.txt" for f in files)
        assert any(f.name == "file2.txt" for f in files)

    def test_copytree(self):
        """Test copying directory tree."""
        source_dir = Path(self.temp_dir) / "source_tree"
        sub_dir = source_dir / "sub"
        sub_dir.mkdir(parents=True)
        (source_dir / "file1.txt").write_text("1")
        (sub_dir / "file2.txt").write_text("2")
        
        dest_dir = Path(self.temp_dir) / "dest_tree"
        
        self.driver.copytree(source_dir, dest_dir)
        
        assert dest_dir.exists()
        assert (dest_dir / "file1.txt").exists()
        assert (dest_dir / "sub" / "file2.txt").exists()

    def test_movetree(self):
        """Test moving directory tree."""
        source_dir = Path(self.temp_dir) / "source_tree"
        sub_dir = source_dir / "sub"
        sub_dir.mkdir(parents=True)
        (source_dir / "file.txt").write_text("Content")
        
        dest_dir = Path(self.temp_dir) / "dest_tree"
        
        self.driver.movetree(source_dir, dest_dir)
        
        assert dest_dir.exists()
        assert (dest_dir / "sub").exists()
        assert not source_dir.exists()


class TestFileDriverUtilityOperations:
    """Test utility operations."""

    def setup_method(self):
        """Setup test driver with temp directory."""
        self.driver = FileDriver(logger=None)
        self.temp_dir = tempfile.mkdtemp()

    def teardown_method(self):
        """Cleanup temp directory."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_glob(self):
        """Test glob pattern matching."""
        dir_path = Path(self.temp_dir)
        (dir_path / "test1.txt").write_text("1")
        (dir_path / "test2.txt").write_text("2")
        (dir_path / "other.log").write_text("log")
        
        matches = self.driver.glob("*.txt", root=dir_path)
        
        assert len(matches) == 2
        assert all(m.suffix == ".txt" for m in matches)

    def test_glob_no_root(self):
        """Test glob without root uses current directory."""
        with patch('pathlib.Path.cwd') as mock_cwd:
            mock_path = Mock()
            mock_path.glob.return_value = [Path("file.txt")]
            mock_cwd.return_value = mock_path
            
            matches = self.driver.glob("*.txt")
            
            mock_path.glob.assert_called_once_with("*.txt")
            assert len(matches) == 1

    def test_hash_file(self):
        """Test file hashing."""
        file_path = Path(self.temp_dir) / "hash_me.txt"
        file_path.write_text("Hash this content")
        
        hash_value = self.driver.hash_file(file_path)
        
        # SHA256 hash of "Hash this content"
        expected = "4f361c36c0ae08de9c6f684bce62f31d50403ec2f17d85046711df9795c4ab6d"
        assert hash_value == expected

    def test_hash_file_different_algorithm(self):
        """Test file hashing with different algorithm."""
        file_path = Path(self.temp_dir) / "hash_me.txt"
        file_path.write_text("Hash this content")
        
        hash_value = self.driver.hash_file(file_path, algorithm="md5")
        
        # MD5 hash of "Hash this content"
        expected = "fce976754d05db9496b56a963e98d72e"
        assert hash_value == expected

    def test_open_file(self):
        """Test opening a file."""
        file_path = Path(self.temp_dir) / "open_me.txt"
        file_path.write_text("Open me")
        
        with self.driver.open_file(file_path, 'r') as f:
            content = f.read()
        
        assert content == "Open me"


class TestFileDriverCommandExecution:
    """Test command execution routing."""

    def setup_method(self):
        """Setup test driver."""
        self.driver = FileDriver(logger=None)

    def test_execute_command_read(self):
        """Test execute_command for read operation."""
        request = Mock()
        request.operation = "read"
        request.path = "/some/file"
        
        with patch.object(self.driver, 'read_file') as mock_read:
            mock_read.return_value = "content"
            
            result = self.driver.execute_command(request)
            
            assert result == "content"
            mock_read.assert_called_once_with("/some/file")

    def test_execute_command_write(self):
        """Test execute_command for write operation."""
        request = Mock()
        request.operation = "write"
        request.path = "/some/file"
        request.content = "new content"
        
        with patch.object(self.driver, 'create_file') as mock_create:
            self.driver.execute_command(request)
            
            mock_create.assert_called_once_with("/some/file", "new content")

    def test_execute_command_copy(self):
        """Test execute_command for copy operation."""
        request = Mock()
        request.operation = "copy"
        request.source = "/source"
        request.destination = "/dest"
        
        with patch.object(self.driver, 'copy') as mock_copy:
            self.driver.execute_command(request)
            
            mock_copy.assert_called_once_with("/source", "/dest")

    def test_execute_command_invalid(self):
        """Test execute_command with invalid operation."""
        request = Mock()
        request.operation = "invalid"
        
        with pytest.raises(ValueError, match="Invalid file operation request"):
            self.driver.execute_command(request)

    def test_execute_command_no_operation(self):
        """Test execute_command with no operation attribute."""
        request = Mock(spec=[])
        
        with pytest.raises(ValueError, match="Invalid file operation request"):
            self.driver.execute_command(request)


class TestFileDriverDockerOperations:
    """Test Docker-specific operations."""

    def setup_method(self):
        """Setup test driver."""
        self.driver = FileDriver(logger=None)

    def test_docker_cp_without_driver(self):
        """Test docker_cp without docker driver raises error."""
        with pytest.raises(RuntimeError, match="Docker driver must be provided"):
            self.driver.docker_cp("container", "/container/path", "/host/path")

    def test_docker_cp_from_container(self):
        """Test docker_cp from container to host."""
        mock_docker_driver = Mock()
        
        self.driver.docker_cp(
            "mycontainer",
            "/app/file.txt",
            "/host/path",
            from_container=True,
            docker_driver=mock_docker_driver
        )
        
        mock_docker_driver.cp.assert_called_once_with(
            "mycontainer",
            "/app/file.txt",
            "/host/path",
            True
        )

    def test_docker_cp_to_container(self):
        """Test docker_cp from host to container."""
        mock_docker_driver = Mock()
        
        self.driver.docker_cp(
            "mycontainer",
            "/app/file.txt",
            "/host/path",
            from_container=False,
            docker_driver=mock_docker_driver
        )
        
        mock_docker_driver.cp.assert_called_once_with(
            "mycontainer",
            "/app/file.txt",
            "/host/path",
            False
        )


class TestFileDriverPrivateMethods:
    """Test private helper methods."""

    def setup_method(self):
        """Setup test driver."""
        self.driver = FileDriver(logger=None)

    def test_notify_vscode_of_change(self):
        """Test VSCode notification method."""
        with patch('os.utime') as mock_utime:
            path = Path("/some/file")
            self.driver._notify_vscode_of_change(path)
            
            mock_utime.assert_called_once_with(path, None)

    def test_notify_vscode_of_change_error_ignored(self):
        """Test VSCode notification errors are ignored."""
        with patch('os.utime', side_effect=Exception("Error")):
            path = Path("/some/file")
            # Should not raise
            self.driver._notify_vscode_of_change(path)