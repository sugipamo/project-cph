"""Mock file system implementation for testing."""
from pathlib import Path
from typing import Dict, List, Set

from src.operations.interfaces.filesystem_interface import FileSystemInterface


class MockFileSystem(FileSystemInterface):
    """Mock file system that simulates file operations in memory."""

    def __init__(self):
        """Initialize mock file system."""
        self.files: Set[Path] = set()
        self.directories: Set[Path] = set()
        self.file_contents: Dict[Path, str] = {}

    def exists(self, path: Path) -> bool:
        """Check if a path exists."""
        return path in self.files or path in self.directories

    def is_file(self, path: Path) -> bool:
        """Check if a path is a file."""
        return path in self.files

    def is_dir(self, path: Path) -> bool:
        """Check if a path is a directory."""
        return path in self.directories

    def iterdir(self, path: Path) -> List[Path]:
        """List contents of a directory."""
        if not self.is_dir(path):
            return []

        contents = []
        path_str = str(path)

        # Find direct children
        for file_path in self.files:
            file_str = str(file_path)
            if file_str.startswith(path_str + "/"):
                relative = file_str[len(path_str) + 1:]
                if "/" not in relative:  # Direct child, not nested
                    contents.append(file_path)

        for dir_path in self.directories:
            dir_str = str(dir_path)
            if dir_str.startswith(path_str + "/"):
                relative = dir_str[len(path_str) + 1:]
                if "/" not in relative:  # Direct child, not nested
                    contents.append(dir_path)

        return contents

    def mkdir(self, path: Path, parents: bool = False, exist_ok: bool = False) -> None:
        """Create a directory."""
        if self.exists(path) and not exist_ok:
            raise FileExistsError(f"Directory {path} already exists")

        if parents:
            # Create parent directories
            current = path
            parents_to_create = []
            while current.parent != current:
                if not self.exists(current.parent):
                    parents_to_create.append(current.parent)
                current = current.parent

            # Create parents in order
            for parent in reversed(parents_to_create):
                self.directories.add(parent)

        self.directories.add(path)

    # Helper methods for testing
    def add_file(self, path: Path, content: str = "") -> None:
        """Add a file to the mock filesystem."""
        self.files.add(path)
        self.file_contents[path] = content

        # Ensure parent directories exist
        parent = path.parent
        while parent != Path('.') and parent != Path('/'):
            self.directories.add(parent)
            parent = parent.parent

    def add_directory(self, path: Path) -> None:
        """Add a directory to the mock filesystem."""
        self.directories.add(path)

        # Ensure parent directories exist
        parent = path.parent
        while parent != Path('.') and parent != Path('/'):
            self.directories.add(parent)
            parent = parent.parent

    def clear(self) -> None:
        """Clear all files and directories."""
        self.files.clear()
        self.directories.clear()
        self.file_contents.clear()

    def get_file_content(self, path: Path) -> str:
        """Get content of a file."""
        return self.file_contents.get(path, "")

    def list_all_files(self) -> List[Path]:
        """List all files in the filesystem."""
        return list(self.files)

    def list_all_directories(self) -> List[Path]:
        """List all directories in the filesystem."""
        return list(self.directories)
