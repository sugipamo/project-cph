"""Local file system driver implementation."""
import os
import shutil
from pathlib import Path
from shutil import copy2
from typing import Any, Optional, TextIO

from src.infrastructure.drivers.file.file_driver import FileDriver


class LocalFileDriver(FileDriver):
    """Local file system driver using Python's built-in file operations."""

    def __init__(self, base_dir: Path = Path(".")):
        super().__init__(base_dir)

    def _move_impl(self, src_path: Path, dst_path: Path) -> None:
        """Move file using shutil.move for better cross-filesystem support."""
        shutil.move(str(src_path), str(dst_path))

    def _copy_impl(self, src_path: Path, dst_path: Path) -> None:
        """Copy file with VSCode change detection support."""
        # Remove existing file for better VSCode change detection
        if dst_path.exists():
            dst_path.unlink()
        copy2(src_path, dst_path)
        # Explicitly update timestamp for VSCode notification
        os.utime(dst_path)

    def _exists_impl(self, path: Path) -> bool:
        """Check if file exists."""
        return path.exists()

    def _create_impl(self, path: Path, content: str) -> None:
        """Create file with VSCode change detection support."""
        # Remove existing file for better VSCode change detection
        if path.exists():
            path.unlink()
        with path.open("w", encoding="utf-8") as f:
            f.write(content)
        # Explicitly update timestamp for VSCode notification
        os.utime(path)

    def _copytree_impl(self, src_path: Path, dst_path: Path) -> None:
        """Copy directory tree."""
        shutil.copytree(src_path, dst_path, dirs_exist_ok=True)

    def _rmtree_impl(self, p: Path) -> None:
        """Remove directory tree or file."""
        if p.is_dir():
            shutil.rmtree(p)
        elif p.exists():
            p.unlink()

    def _remove_impl(self, p: Path) -> None:
        """Remove file."""
        if p.exists():
            p.unlink()

    def open(self, path: Path, mode: str = "r", encoding: Optional[str] = None) -> TextIO:
        """Open file and return file object."""
        return Path(path).open(mode=mode, encoding=encoding)

    def docker_cp(self, src: str, dst: str, container: str, to_container: bool = True, docker_driver: Any = None) -> Any:
        """Copy files to/from Docker container."""
        if docker_driver is None:
            raise ValueError("docker_driver is required")
        return docker_driver.cp(src, dst, container, to_container=to_container)

    def list_files(self, base_dir: Path) -> list[str]:
        """List all files under specified directory."""
        base = self.base_dir / base_dir
        result = []
        for root, _dirs, files in os.walk(base):
            for file in files:
                result.append(str(Path(root) / file))
        return result
