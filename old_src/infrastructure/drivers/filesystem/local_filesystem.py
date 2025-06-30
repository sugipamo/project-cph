"""Local file system implementation."""
from pathlib import Path
from typing import List

# 互換性維持: configuration層への逆方向依存を削除、依存性注入で解決
# TypeSafeConfigNodeManager機能は外部から注入される必要があります
from old_src.operations.interfaces.filesystem_interface import FileSystemInterface


class FileSystemError(Exception):
    """ファイルシステム操作でのエラー"""
    pass


class LocalFileSystem(FileSystemInterface):
    """Local file system implementation of FileSystemInterface."""

    def __init__(self, config_provider):
        """Initialize LocalFileSystem with configuration provider."""
        self.config_provider = config_provider

    def exists(self, path: Path) -> bool:
        """Check if a path exists."""
        return path.exists()

    def is_file(self, path: Path) -> bool:
        """Check if a path is a file."""
        return path.is_file()

    def is_dir(self, path: Path) -> bool:
        """Check if a path is a directory."""
        return path.is_dir()

    def iterdir(self, path: Path) -> List[Path]:
        """List contents of a directory."""
        try:
            return list(path.iterdir())
        except (OSError, PermissionError) as e:
            if self.config_provider is None:
                raise FileSystemError(f"Failed to list directory contents: {e}") from e

            error_action = self.config_provider.resolve_config(
                ['filesystem_config', 'error_handling', 'permission_denied_action'],
                str
            )
            if error_action == 'error':
                raise FileSystemError(f"Failed to list directory contents: {e}") from e
            raise FileSystemError(f"Invalid error action configured: {error_action}. Must be 'error'.") from e

    def mkdir(self, path: Path, parents: bool, exist_ok: bool) -> None:
        """Create a directory."""
        path.mkdir(parents=parents, exist_ok=exist_ok)


    def delete_file(self, path: Path) -> bool:
        """Delete a file."""
        raise NotImplementedError("delete_file is not implemented")

    def create_directory(self, path: Path) -> bool:
        """Create a directory."""
        raise NotImplementedError("create_directory is not implemented")
