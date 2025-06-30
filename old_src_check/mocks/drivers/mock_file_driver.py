"""Mock file driver for testing behavior verification."""
from contextlib import contextmanager
from io import StringIO
from pathlib import Path
from typing import Any, Optional

from old_src.infrastructure.drivers.file.file_driver import FileDriver


class MockFileDriver(FileDriver):
    """Mock driver for behavior verification
    - Detailed operation history recording
    - Return expected values
    - Internal state simulation
    """

    def __init__(self, base_dir: Path):
        super().__init__(logger=None)
        self.base_dir = base_dir
        # Operation history (for behavior verification)
        self.operations: list[tuple[str, ...]] = []
        self.call_count: dict[str, int] = {}

        # Internal state simulation
        self.files: set[Path] = set()
        self.contents: dict[Path, str] = {}

        # Expected value settings
        self.expected_results: dict[str, Any] = {}
        self.file_exists_map: dict[Path, bool] = {}

    def _record_operation(self, operation: str, *args) -> None:
        """Record operation and count calls"""
        self.operations.append((operation, *args))
        if operation not in self.call_count:
            self.call_count[operation] = 0
        self.call_count[operation] = self.call_count[operation] + 1

    def assert_operation_called(self, operation: str, times: Optional[int]) -> None:
        """Verify that specified operation was called"""
        if operation not in self.call_count:
            count = 0
        else:
            count = self.call_count[operation]
        if times is None:
            assert count > 0, f"Operation '{operation}' was not called"
        else:
            assert count == times, f"Operation '{operation}' was called {count} times, expected {times}"

    def assert_operation_called_with(self, operation: str, *expected_args) -> None:
        """Verify that specified operation was called with specific arguments"""
        matching_calls = [op for op in self.operations if op[0] == operation and op[1:] == expected_args]
        assert len(matching_calls) > 0, f"Operation '{operation}' with args {expected_args} was not found in {self.operations}"

    def set_file_exists(self, path: str, exists: bool) -> None:
        """Set file existence state"""
        abs_path = self.base_dir / Path(path)
        self.file_exists_map[abs_path] = exists
        if exists:
            self.files.add(abs_path)
        elif abs_path in self.files:
            self.files.remove(abs_path)

    def _move_impl(self, src_path: Path, dst_path: Path) -> None:
        # src_path and dst_path are already resolved absolute paths
        self.ensure_parent_dir(dst_path)
        self._record_operation("move", src_path, dst_path)
        if src_path in self.files:
            self.files.remove(src_path)
            self.files.add(dst_path)
            self.contents[dst_path] = self.contents.pop(src_path, "")

    def _copy_impl(self, src_path: Path, dst_path: Path) -> None:
        # src_path and dst_path are already resolved absolute paths
        self.ensure_parent_dir(dst_path)
        if src_path not in self.files:
            raise FileNotFoundError(f"MockFileDriver: {src_path} does not exist")
        self._record_operation("copy", src_path, dst_path)
        if src_path in self.files:
            self.files.add(dst_path)
            self.contents[dst_path] = self.contents[src_path]

    def _exists_impl(self, path: Path) -> bool:
        # If already absolute path, don't add base_dir
        if isinstance(path, Path) and path.is_absolute():
            abs_path = path
        else:
            abs_path = self.base_dir / Path(path)
        self._record_operation("exists", abs_path)
        return abs_path in self.files

    def _create_impl(self, path: Path, content: str) -> None:
        """Create file with content"""
        self._record_operation("create", path, content)
        self.files.add(path)
        self.contents[path] = content

    def _copytree_impl(self, src_path: Path, dst_path: Path) -> None:
        """Copy directory tree"""
        self._record_operation("copytree", src_path, dst_path)
        # Simplified implementation for mock
        self.files.add(dst_path)

    def _movetree_impl(self, src_path: Path, dst_path: Path) -> None:
        """Move directory tree"""
        self._record_operation("movetree", src_path, dst_path)
        # Simplified implementation for mock
        if src_path in self.files:
            self.files.remove(src_path)
        if src_path in self.contents:
            self.contents[dst_path] = self.contents.pop(src_path)
        self.files.add(dst_path)

    def _rmtree_impl(self, path: Path) -> None:
        """Remove directory tree"""
        self._record_operation("rmtree", path)
        if path in self.files:
            self.files.remove(path)
        if path in self.contents:
            del self.contents[path]

    def _remove_impl(self, path: Path) -> None:
        """Remove file"""
        self._record_operation("remove", path)
        if path in self.files:
            self.files.remove(path)
        if path in self.contents:
            del self.contents[path]

    def makedirs(self, path: Path, exist_ok: bool = True) -> None:
        """Create directories (mock implementation)."""
        target_path = self.resolve_path(path)
        self._record_operation("makedirs", target_path, exist_ok)
        # Mock implementation - just add to files set to indicate it exists
        self.files.add(target_path)

    def open_file(self, path: str, mode: str = 'r', encoding: Optional[str] = 'utf-8', **kwargs):
        """Mock file open"""

        # Convert to absolute path
        if isinstance(path, str):
            path_obj = self.base_dir / Path(path)
        else:
            path_obj = path

        self._record_operation("open", path_obj, mode)

        @contextmanager
        def mock_file():
            if mode.startswith('r'):
                if path_obj not in self.files:
                    raise FileNotFoundError(f"MockFileDriver: {path_obj} does not exist")
                content = self.contents[path_obj]
                yield StringIO(content)
            elif mode.startswith('w'):
                content_io = StringIO()
                yield content_io
                # After writing, save content
                written_content = content_io.getvalue()
                self.files.add(path_obj)
                self.contents[path_obj] = written_content
            else:
                raise NotImplementedError(f"Mode '{mode}' not implemented in MockFileDriver")

        return mock_file()

    def docker_cp(self, src: str, dst: str, container: str, to_container: bool, docker_driver: Any):
        """Mock Docker copy"""
        self._record_operation("docker_cp", src, dst, container, to_container)
        # Check if source file exists
        src_path = Path(src) if Path(src).is_absolute() else self.base_dir / Path(src)
        if src_path not in self.files:
            raise FileNotFoundError(f"MockFileDriver: {src_path} does not exist")
        return f"mock_docker_cp_{container}_{src}_{dst}"

    def hash_file(self, path: Path) -> str:
        """Mock file hash calculation"""
        self._record_operation("hash_file", path)
        if path not in self.files:
            raise FileNotFoundError(f"MockFileDriver: {path} does not exist")
        # Return mock hash based on file content
        content = self.contents[path]
        return f"mock_hash_{hash(content)}"

    def list_files(self, base_dir: Path) -> list[Path]:
        """List all files under directory"""
        self._record_operation("list_files", base_dir)
        base = self.base_dir / base_dir
        return [f for f in self.files if str(f).startswith(str(base))]

    def _list_files_recursive_impl(self, path: Path) -> list[Path]:
        """Mock implementation for listing files recursively"""
        self._record_operation("list_files_recursive", path)
        # Return files that are under the given path
        return [f for f in self.files if str(f).startswith(str(path))]
