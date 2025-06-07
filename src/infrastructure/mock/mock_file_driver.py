"""Mock file driver for testing behavior verification."""
from pathlib import Path
from typing import Dict, Set, Any, Optional, List, Tuple
from src.infrastructure.drivers.file.file_driver import FileDriver


class MockFileDriver(FileDriver):
    """
    Mock driver for behavior verification
    - Detailed operation history recording
    - Return expected values
    - Internal state simulation
    """
    
    def __init__(self, base_dir: Path = Path(".")):
        super().__init__(base_dir)
        # Operation history (for behavior verification)
        self.operations: List[Tuple[str, ...]] = []
        self.call_count: Dict[str, int] = {}
        
        # Internal state simulation
        self.files: Set[Path] = set()
        self.contents: Dict[Path, str] = {}
        
        # Expected value settings
        self.expected_results: Dict[str, Any] = {}
        self.file_exists_map: Dict[Path, bool] = {}

    def _record_operation(self, operation: str, *args) -> None:
        """Record operation and count calls"""
        self.operations.append((operation, *args))
        self.call_count[operation] = self.call_count.get(operation, 0) + 1

    def assert_operation_called(self, operation: str, times: Optional[int] = None) -> None:
        """Verify that specified operation was called"""
        count = self.call_count.get(operation, 0)
        if times is None:
            assert count > 0, f"Operation '{operation}' was not called"
        else:
            assert count == times, f"Operation '{operation}' was called {count} times, expected {times}"

    def assert_operation_called_with(self, operation: str, *expected_args) -> None:
        """Verify that specified operation was called with specific arguments"""
        matching_calls = [op for op in self.operations if op[0] == operation and op[1:] == expected_args]
        assert len(matching_calls) > 0, f"Operation '{operation}' with args {expected_args} was not found in {self.operations}"

    def set_file_exists(self, path: str, exists: bool = True) -> None:
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
            self.contents[dst_path] = self.contents[src_path] if src_path in self.contents else ""

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

    def open(self, path: Path, mode: str = "r", encoding: Optional[str] = None):
        """Mock file open"""
        self._record_operation("open", path, mode)
        # Return mock file object or raise error
        if mode.startswith('r') and path not in self.files:
            raise FileNotFoundError(f"MockFileDriver: {path} does not exist")
        # For mock purposes, return None
        return None

    def docker_cp(self, src: str, dst: str, container: str, to_container: bool = True, docker_driver: Any = None):
        """Mock Docker copy"""
        self._record_operation("docker_cp", src, dst, container, to_container)
        return None

    def list_files(self, base_dir: Path) -> List[Path]:
        """List all files under directory"""
        self._record_operation("list_files", base_dir)
        base = self.base_dir / base_dir
        return [f for f in self.files if str(f).startswith(str(base))]