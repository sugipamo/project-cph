"""Integrated file driver combining FileDriver and LocalFileDriver.

This module combines the abstract FileDriver and LocalFileDriver into a single
concrete implementation to reduce file count and complexity.
"""
import hashlib
import os
import shutil
from pathlib import Path
from typing import Any, Optional, TextIO

from src.infrastructure.drivers.generic.base_driver import ExecutionDriverInterface


class IntegratedFileDriver(ExecutionDriverInterface):
    """Integrated file system driver with all file operations.
    
    Combines functionality from FileDriver (abstract) and LocalFileDriver (concrete)
    into a single implementation.
    """

    def __init__(self, base_dir: Optional[Path] = None):
        """Initialize with optional base directory.
        
        Args:
            base_dir: Base directory for relative paths. If None, uses current directory.
        """
        self.base_dir = Path(base_dir) if base_dir else Path('.')
        # These are for dynamic operations compatibility
        self.path = None
        self.dst_path = None

    def execute_command(self, request: Any) -> Any:
        """Execute a file operation request."""
        # This method is for compatibility with ExecutionDriverInterface
        # Actual execution happens through specific methods
        pass

    def validate(self, request: Any) -> bool:
        """Validate if this driver can handle the request."""
        # For now, always return True for file requests
        return True

    def resolve_path(self, path: Path) -> Path:
        """Resolve path to absolute path.
        
        Args:
            path: Path to resolve
            
        Returns:
            Absolute path if input is absolute, else relative to base_dir
        """
        path = Path(path)
        if path.is_absolute():
            return path
        return self.base_dir / path

    def exists(self, path: Path) -> bool:
        """Check if file or directory exists."""
        resolved_path = self.resolve_path(path)
        return resolved_path.exists()

    def isdir(self, path: Path) -> bool:
        """Check if path is a directory."""
        resolved_path = self.resolve_path(path)
        return resolved_path.is_dir()

    def is_file(self, path: Path) -> bool:
        """Check if path is a file."""
        resolved_path = self.resolve_path(path)
        return resolved_path.is_file()

    def create_file(self, path: Path, content: str) -> None:
        """Create file with content."""
        resolved_path = self.resolve_path(path)
        self.ensure_parent_dir(resolved_path)
        
        # Remove existing file for better VSCode change detection
        if resolved_path.exists():
            resolved_path.unlink()
        
        with resolved_path.open("w", encoding="utf-8") as f:
            f.write(content)
        
        # Explicitly update timestamp for VSCode notification
        os.utime(resolved_path)

    def copy(self, src_path: Path, dst_path: Path) -> None:
        """Copy file from source to destination."""
        resolved_src = self.resolve_path(src_path)
        resolved_dst = self.resolve_path(dst_path)
        self.ensure_parent_dir(resolved_dst)
        
        # Remove existing file for better VSCode change detection
        if resolved_dst.exists():
            resolved_dst.unlink()
        
        shutil.copy2(resolved_src, resolved_dst)
        
        # Explicitly update timestamp for VSCode notification
        os.utime(resolved_dst)

    def move(self, src_path: Path, dst_path: Path) -> None:
        """Move file from source to destination."""
        resolved_src = self.resolve_path(src_path)
        resolved_dst = self.resolve_path(dst_path)
        self.ensure_parent_dir(resolved_dst)
        
        shutil.move(str(resolved_src), str(resolved_dst))

    def remove(self, path: Path) -> None:
        """Remove file."""
        resolved_path = self.resolve_path(path)
        if resolved_path.exists():
            resolved_path.unlink()

    def makedirs(self, path: Path, exist_ok: bool = True) -> None:
        """Create directories."""
        resolved_path = self.resolve_path(path)
        resolved_path.mkdir(parents=True, exist_ok=exist_ok)

    def mkdir(self, path: Path) -> None:
        """Create single directory."""
        resolved_path = self.resolve_path(path)
        resolved_path.mkdir(parents=True, exist_ok=True)

    def list_files(self, base_dir: Path) -> list[str]:
        """List all files under specified directory."""
        resolved_base = self.resolve_path(base_dir)
        result = []
        for root, _dirs, files in os.walk(resolved_base):
            for file in files:
                result.append(str(Path(root) / file))
        return result

    def list_files_recursive(self, path: Path) -> list[Path]:
        """List all files recursively in directory."""
        resolved_path = self.resolve_path(path)
        result = []
        for root, _dirs, files in os.walk(resolved_path):
            for file in files:
                result.append(Path(root) / file)
        return result

    def copytree(self, src_path: Path, dst_path: Path) -> None:
        """Copy directory tree."""
        resolved_src = self.resolve_path(src_path)
        resolved_dst = self.resolve_path(dst_path)
        
        if resolved_src == resolved_dst:
            return
            
        self.ensure_parent_dir(resolved_dst)
        shutil.copytree(resolved_src, resolved_dst, dirs_exist_ok=True)

    def movetree(self, src_path: Path, dst_path: Path) -> None:
        """Move directory tree."""
        resolved_src = self.resolve_path(src_path)
        resolved_dst = self.resolve_path(dst_path)
        
        if resolved_src == resolved_dst:
            return
            
        self.ensure_parent_dir(resolved_dst)
        
        if resolved_dst.exists():
            shutil.rmtree(resolved_dst)
        
        shutil.move(str(resolved_src), str(resolved_dst))

    def rmtree(self, path: Path) -> None:
        """Remove directory tree or file."""
        resolved_path = self.resolve_path(path)
        
        if resolved_path.is_dir():
            shutil.rmtree(resolved_path)
        elif resolved_path.exists():
            resolved_path.unlink()

    def touch(self, path: Path) -> None:
        """Touch file (create or update timestamp)."""
        resolved_path = self.resolve_path(path)
        resolved_path.parent.mkdir(parents=True, exist_ok=True)
        resolved_path.touch(exist_ok=True)

    def glob(self, pattern: str) -> list[Path]:
        """Find files matching pattern."""
        return list(self.base_dir.glob(pattern))

    def hash_file(self, path: Path, algo: str = "md5") -> str:
        """Calculate file hash."""
        h = hashlib.new(algo)
        resolved_path = self.resolve_path(path)
        
        with open(resolved_path, 'rb') as f:
            while True:
                chunk = f.read(8192)
                if not chunk:
                    break
                h.update(chunk)
        
        return h.hexdigest()

    def open(self, path: Path, mode: str = "r", encoding: Optional[str] = "utf-8") -> TextIO:
        """Open file and return file object."""
        resolved_path = self.resolve_path(path)
        return resolved_path.open(mode=mode, encoding=encoding)

    def read_file(self, path: str) -> str:
        """Read file contents as string.
        
        Args:
            path: File path to read
            
        Returns:
            File contents as string
        """
        resolved_path = self.resolve_path(Path(path))
        with resolved_path.open("r", encoding="utf-8") as f:
            return f.read()

    def ensure_parent_dir(self, path: Path) -> None:
        """Ensure parent directory exists."""
        parent = Path(path).parent
        parent.mkdir(parents=True, exist_ok=True)

    def docker_cp(self, src: str, dst: str, container: str, to_container: bool = True, docker_driver: Any = None) -> Any:
        """Copy files to/from Docker container.
        
        Args:
            src: Source path
            dst: Destination path
            container: Container name
            to_container: True to copy to container, False to copy from container
            docker_driver: Docker driver instance
            
        Returns:
            Result of docker cp operation
            
        Raises:
            ValueError: If docker_driver is not provided
        """
        if docker_driver is None:
            raise ValueError("docker_driver is required for docker_cp operation")
        
        return docker_driver.cp(src, dst, container, to_container=to_container)