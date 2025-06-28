"""Consolidated file system driver."""
import hashlib
import os
import shutil
from pathlib import Path
from typing import Any, List, Optional, Union

from src.infrastructure.drivers.base_driver import BaseDriverImplementation
from src.infrastructure.di_container import DIContainer


class FileDriver(BaseDriverImplementation):
    """Unified file system operations driver."""
    
    def __init__(self, container: Optional[DIContainer] = None):
        """Initialize file driver.
        
        Args:
            container: Optional DI container for dependency resolution
        """
        super().__init__(container)
        self._docker_driver = None
    
    @property
    def docker_driver(self):
        """Lazy load Docker driver for docker_cp operations."""
        if self._docker_driver is None and self.container:
            from src.infrastructure.di_container import DIKey
            self._docker_driver = self.container.resolve(DIKey.DOCKER_DRIVER)
        return self._docker_driver
    
    def execute_command(self, request: Any) -> Any:
        """Execute a file operation request.
        
        Routes to appropriate method based on request type.
        """
        if hasattr(request, 'operation'):
            op = request.operation
            if op == 'read':
                return self.read_file(request.path)
            elif op == 'write':
                return self.create_file(request.path, request.content)
            elif op == 'copy':
                return self.copy(request.source, request.destination)
            elif op == 'move':
                return self.move(request.source, request.destination)
            elif op == 'remove':
                return self.remove(request.path)
            elif op == 'mkdir':
                return self.mkdir(request.path)
            elif op == 'exists':
                return self.exists(request.path)
        
        raise ValueError("Invalid file operation request")
    
    def validate(self, request: Any) -> bool:
        """Validate if this driver can handle the request."""
        return hasattr(request, 'operation') and request.operation in [
            'read', 'write', 'copy', 'move', 'remove', 'mkdir', 'exists',
            'isdir', 'is_file', 'list_files', 'glob', 'hash'
        ]
    
    # Path operations
    
    def resolve_path(self, path: Union[str, Path]) -> Path:
        """Resolve a path to absolute path.
        
        Args:
            path: Path to resolve
            
        Returns:
            Absolute Path object
        """
        p = Path(path)
        return p.resolve()
    
    def exists(self, path: Union[str, Path]) -> bool:
        """Check if a path exists."""
        return self.resolve_path(path).exists()
    
    def isdir(self, path: Union[str, Path]) -> bool:
        """Check if a path is a directory."""
        return self.resolve_path(path).is_dir()
    
    def is_file(self, path: Union[str, Path]) -> bool:
        """Check if a path is a file."""
        return self.resolve_path(path).is_file()
    
    # File operations
    
    def create_file(self, path: Union[str, Path], content: str = "", 
                   create_parents: bool = True) -> None:
        """Create or overwrite a file with content.
        
        Args:
            path: File path
            content: Content to write
            create_parents: Create parent directories if they don't exist
        """
        file_path = self.resolve_path(path)
        
        if create_parents:
            file_path.parent.mkdir(parents=True, exist_ok=True)
        
        self.log_debug(f"Writing file: {file_path}")
        file_path.write_text(content, encoding='utf-8')
        
        # Touch to notify VSCode of changes
        self._notify_vscode_of_change(file_path)
    
    def read_file(self, path: Union[str, Path]) -> str:
        """Read file content.
        
        Args:
            path: File path to read
            
        Returns:
            File content as string
        """
        file_path = self.resolve_path(path)
        self.log_debug(f"Reading file: {file_path}")
        return file_path.read_text(encoding='utf-8')
    
    def copy(self, source: Union[str, Path], destination: Union[str, Path]) -> None:
        """Copy a file or directory.
        
        Args:
            source: Source path
            destination: Destination path
        """
        src = self.resolve_path(source)
        dst = self.resolve_path(destination)
        
        self.log_debug(f"Copying: {src} -> {dst}")
        
        if src.is_dir():
            shutil.copytree(src, dst, dirs_exist_ok=True)
        else:
            # Create parent directories if needed
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
        
        self._notify_vscode_of_change(dst)
    
    def move(self, source: Union[str, Path], destination: Union[str, Path]) -> None:
        """Move a file or directory.
        
        Args:
            source: Source path
            destination: Destination path
        """
        src = self.resolve_path(source)
        dst = self.resolve_path(destination)
        
        self.log_debug(f"Moving: {src} -> {dst}")
        
        # Create parent directories if needed
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(src), str(dst))
        
        self._notify_vscode_of_change(dst)
    
    def remove(self, path: Union[str, Path]) -> None:
        """Remove a file or directory.
        
        Args:
            path: Path to remove
        """
        file_path = self.resolve_path(path)
        
        self.log_debug(f"Removing: {file_path}")
        
        if file_path.is_dir():
            shutil.rmtree(file_path)
        elif file_path.exists():
            file_path.unlink()
    
    def touch(self, path: Union[str, Path]) -> None:
        """Create an empty file or update its timestamp.
        
        Args:
            path: File path
        """
        file_path = self.resolve_path(path)
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.touch()
        self._notify_vscode_of_change(file_path)
    
    # Directory operations
    
    def mkdir(self, path: Union[str, Path], exist_ok: bool = True) -> None:
        """Create a directory.
        
        Args:
            path: Directory path
            exist_ok: Don't raise error if directory exists
        """
        dir_path = self.resolve_path(path)
        self.log_debug(f"Creating directory: {dir_path}")
        dir_path.mkdir(exist_ok=exist_ok)
    
    def makedirs(self, path: Union[str, Path], exist_ok: bool = True) -> None:
        """Create a directory and all parent directories.
        
        Args:
            path: Directory path
            exist_ok: Don't raise error if directory exists
        """
        dir_path = self.resolve_path(path)
        self.log_debug(f"Creating directory tree: {dir_path}")
        dir_path.mkdir(parents=True, exist_ok=exist_ok)
    
    def rmtree(self, path: Union[str, Path]) -> None:
        """Remove a directory tree.
        
        Args:
            path: Directory path to remove
        """
        dir_path = self.resolve_path(path)
        self.log_debug(f"Removing directory tree: {dir_path}")
        shutil.rmtree(dir_path)
    
    def list_files(self, path: Union[str, Path], recursive: bool = False) -> List[Path]:
        """List files in a directory.
        
        Args:
            path: Directory path
            recursive: List files recursively
            
        Returns:
            List of file paths
        """
        dir_path = self.resolve_path(path)
        
        if recursive:
            return [f for f in dir_path.rglob("*") if f.is_file()]
        else:
            return [f for f in dir_path.iterdir() if f.is_file()]
    
    def copytree(self, source: Union[str, Path], destination: Union[str, Path]) -> None:
        """Copy a directory tree.
        
        Args:
            source: Source directory
            destination: Destination directory
        """
        src = self.resolve_path(source)
        dst = self.resolve_path(destination)
        
        self.log_debug(f"Copying tree: {src} -> {dst}")
        shutil.copytree(src, dst, dirs_exist_ok=True)
        self._notify_vscode_of_change(dst)
    
    def movetree(self, source: Union[str, Path], destination: Union[str, Path]) -> None:
        """Move a directory tree.
        
        Args:
            source: Source directory
            destination: Destination directory
        """
        src = self.resolve_path(source)
        dst = self.resolve_path(destination)
        
        self.log_debug(f"Moving tree: {src} -> {dst}")
        shutil.move(str(src), str(dst))
        self._notify_vscode_of_change(dst)
    
    # Utility operations
    
    def glob(self, pattern: str, root: Optional[Union[str, Path]] = None) -> List[Path]:
        """Find files matching a glob pattern.
        
        Args:
            pattern: Glob pattern
            root: Root directory for search (default: current directory)
            
        Returns:
            List of matching paths
        """
        if root:
            root_path = self.resolve_path(root)
        else:
            root_path = Path.cwd()
        
        return list(root_path.glob(pattern))
    
    def hash_file(self, path: Union[str, Path], algorithm: str = "sha256") -> str:
        """Calculate hash of a file.
        
        Args:
            path: File path
            algorithm: Hash algorithm (default: sha256)
            
        Returns:
            Hex digest of the file hash
        """
        file_path = self.resolve_path(path)
        
        hash_obj = hashlib.new(algorithm)
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_obj.update(chunk)
        
        return hash_obj.hexdigest()
    
    def open_file(self, path: Union[str, Path], mode: str = 'r', **kwargs):
        """Open a file and return file handle.
        
        Args:
            path: File path
            mode: Open mode
            **kwargs: Additional arguments for open()
            
        Returns:
            File handle
        """
        file_path = self.resolve_path(path)
        return open(file_path, mode, **kwargs)
    
    # Docker-specific operations
    
    def docker_cp(self, container_name: str, container_path: str, 
                  host_path: Union[str, Path], from_container: bool = True) -> None:
        """Copy files between container and host using docker cp.
        
        Args:
            container_name: Container name
            container_path: Path inside container
            host_path: Path on host
            from_container: True to copy from container to host, False for host to container
        """
        if not self.docker_driver:
            raise RuntimeError("Docker driver not available for docker_cp operation")
        
        self.log_info(f"Docker cp: {'from' if from_container else 'to'} container {container_name}")
        
        # Delegate to docker driver
        self.docker_driver.cp(container_name, container_path, host_path, from_container)
    
    # Private helper methods
    
    def _notify_vscode_of_change(self, path: Path) -> None:
        """Touch file to notify VSCode of changes.
        
        VSCode may not detect file changes made programmatically,
        so we touch the file to update its timestamp.
        """
        try:
            os.utime(path, None)
        except Exception:
            # Ignore errors in notification
            pass