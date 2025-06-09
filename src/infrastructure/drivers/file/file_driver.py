"""Abstract base class for file operations.
"""
from abc import abstractmethod
from pathlib import Path
from typing import Any, Optional

from src.infrastructure.drivers.base.base_driver import BaseDriver


class FileDriver(BaseDriver):
    """Abstract base class for file operations.

    Uses template method pattern:
    - Common operations (path resolution, parent directory creation) in base class
    - Actual file operations in concrete classes (_*_impl methods)
    """

    def __init__(self, base_dir: Path = Path(".")):
        self.base_dir = Path(base_dir)
        # path and dst_path are set dynamically during operations
        self.path = None
        self.dst_path = None

    def execute(self, request: Any) -> Any:
        """Execute a file operation request."""
        # This method is for compatibility with BaseDriver
        # Actual execution happens through specific methods

    def validate(self, request: Any) -> bool:
        """Validate if this driver can handle the request."""
        # For now, always return True for file requests
        return True

    def resolve_path(self, path: Optional[Path] = None) -> Path:
        """Resolve path to absolute path."""
        target_path = path if path is not None else self.path
        if target_path is None:
            raise ValueError("Path is not set")
        return self.base_dir / Path(target_path)

    def makedirs(self, path: Optional[Path] = None, exist_ok: bool = True) -> None:
        """Create directories."""
        target_path = self.resolve_path(path)
        target_path.mkdir(parents=True, exist_ok=exist_ok)

    def isdir(self, path: Optional[Path] = None) -> bool:
        """Check if path is a directory."""
        target_path = self.resolve_path(path)
        return target_path.is_dir()


    def list_files_recursive(self, path: Path) -> list[Path]:
        """List all files recursively in directory."""
        resolved_path = self.resolve_path(path)
        return self._list_files_recursive_impl(resolved_path)

    def is_file(self, path: Path) -> bool:
        """Check if path is a file."""
        resolved_path = self.resolve_path(path)
        return resolved_path.is_file()

    @abstractmethod
    def _copytree_impl(self, src_path: Path, dst_path: Path) -> None:
        """Implementation for copying directory tree."""
        pass

    @abstractmethod
    def _rmtree_impl(self, path: Path) -> None:
        """Implementation for removing directory tree."""
        pass

    @abstractmethod
    def _list_files_recursive_impl(self, path: Path) -> list[Path]:
        """Implementation for listing files recursively."""
        pass

    def glob(self, pattern: str) -> list[Path]:
        """Find files matching pattern."""
        return list(self.base_dir.glob(pattern))

    def move(self, src_path: Optional[Path] = None, dst_path: Optional[Path] = None) -> None:
        """Move file (template method)."""
        # Backward compatibility: use self.path and self.dst_path if no args
        if src_path is None:
            src_path = self.path
        if dst_path is None:
            dst_path = self.dst_path

        resolved_src = self.resolve_path(src_path)
        resolved_dst = self.resolve_path(dst_path)
        self.ensure_parent_dir(resolved_dst)
        self._move_impl(resolved_src, resolved_dst)

    @abstractmethod
    def _move_impl(self, src_path: Path, dst_path: Path) -> None:
        """File move implementation (implement in concrete class)."""

    def copy(self, src_path: Optional[Path] = None, dst_path: Optional[Path] = None) -> None:
        """Copy file (template method)."""
        # Backward compatibility: use self.path and self.dst_path if no args
        if src_path is None:
            src_path = self.path
        if dst_path is None:
            dst_path = self.dst_path

        resolved_src = self.resolve_path(src_path)
        resolved_dst = self.resolve_path(dst_path)
        self.ensure_parent_dir(resolved_dst)
        self._copy_impl(resolved_src, resolved_dst)

    @abstractmethod
    def _copy_impl(self, src_path: Path, dst_path: Path) -> None:
        """File copy implementation (implement in concrete class)."""

    def exists(self, path: Optional[Path] = None) -> bool:
        """Check file existence (template method)."""
        # Backward compatibility: use self.path if no arg
        if path is None:
            path = self.path
        resolved_path = self.resolve_path(path)
        return self._exists_impl(resolved_path)

    @abstractmethod
    def _exists_impl(self, path: Path) -> bool:
        """File existence check implementation (implement in concrete class)."""

    def create(self, path: Path, content: str = "") -> None:
        """Create file (template method)."""
        resolved_path = self.resolve_path(path)
        self.ensure_parent_dir(resolved_path)
        self._create_impl(resolved_path, content)

    @abstractmethod
    def _create_impl(self, path: Path, content: str) -> None:
        """File creation implementation (implement in concrete class)."""

    def copytree(self, src_path: Path, dst_path: Path) -> None:
        """Copy directory tree (template method)."""
        resolved_src = self.resolve_path(src_path)
        resolved_dst = self.resolve_path(dst_path)
        if resolved_src == resolved_dst:
            return
        self.ensure_parent_dir(resolved_dst)
        self._copytree_impl(resolved_src, resolved_dst)

    @abstractmethod
    def _copytree_impl(self, src_path: Path, dst_path: Path) -> None:
        """Directory tree copy implementation (implement in concrete class)."""

    def rmtree(self, path: Path) -> None:
        """Remove directory tree (template method)."""
        resolved_path = self.resolve_path(path)
        self._rmtree_impl(resolved_path)

    @abstractmethod
    def _rmtree_impl(self, path: Path) -> None:
        """Directory tree removal implementation (implement in concrete class)."""

    def remove(self, path: Path) -> None:
        """Remove file (template method)."""
        resolved_path = self.resolve_path(path)
        self._remove_impl(resolved_path)

    @abstractmethod
    def _remove_impl(self, path: Path) -> None:
        """File removal implementation (implement in concrete class)."""

    @abstractmethod
    def open(self, path: Path, mode: str = "r", encoding: Optional[str] = None):
        """Open file (implement in concrete class)."""

    def ensure_parent_dir(self, path: Path) -> None:
        """Ensure parent directory exists."""
        parent = Path(path).parent
        parent.mkdir(parents=True, exist_ok=True)

    def hash_file(self, path: Path, algo: str = 'sha256') -> str:
        """Calculate file hash."""
        import hashlib
        h = hashlib.new(algo)
        resolved_path = self.resolve_path(path)
        with open(resolved_path, 'rb') as f:
            while True:
                chunk = f.read(8192)
                if not chunk:
                    break
                h.update(chunk)
        return h.hexdigest()

    @abstractmethod
    def docker_cp(self, src: str, dst: str, container: str, to_container: bool = True, docker_driver=None):
        """Copy files to/from Docker container (implement in concrete class)."""

    def mkdir(self, path: Path) -> None:
        """Create directory."""
        resolved_path = self.resolve_path(path)
        resolved_path.mkdir(parents=True, exist_ok=True)

    def touch(self, path: Path) -> None:
        """Touch file (create or update timestamp)."""
        resolved_path = self.resolve_path(path)
        resolved_path.parent.mkdir(parents=True, exist_ok=True)
        resolved_path.touch(exist_ok=True)

    @abstractmethod
    def list_files(self, base_dir: Path) -> list[Path]:
        """List all files under specified directory (implement in concrete class)."""
