"""Folder mapping system for state transitions."""
from pathlib import Path
from typing import Any, Dict, List

from src.domain.interfaces.filesystem_interface import FileSystemInterface

from ..error_handling.state_definitions import WorkflowContext
from .folder_path_resolver import define_standard_areas, get_area_path


class FolderMapper:
    """Maps logical areas to physical folder structures."""

    def __init__(self, path_vars: Dict[str, str], filesystem: FileSystemInterface):
        """Initialize with path variables and filesystem interface.

        Args:
            path_vars: Path variables from env.json
            filesystem: File system interface for operations
        """
        self.path_vars = path_vars
        self.filesystem = filesystem
        self._areas = define_standard_areas()


    def get_area_path(self, area_name: str, context: WorkflowContext) -> Path:
        """Get the resolved path for an area."""
        return get_area_path(area_name, self._areas, context, self.path_vars)

    def area_exists(self, area_name: str, context: WorkflowContext) -> bool:
        """Check if area path exists."""
        path = self.get_area_path(area_name, context)
        return self.filesystem.exists(path)

    def area_has_files(self, area_name: str, context: WorkflowContext) -> bool:
        """Check if area has any files."""
        path = self.get_area_path(area_name, context)
        if not self.filesystem.exists(path):
            return False

        items = self.filesystem.iterdir(path)
        return any(self.filesystem.is_file(item) for item in items)

    def list_area_files(self, area_name: str, context: WorkflowContext) -> List[Path]:
        """List all files in an area."""
        path = self.get_area_path(area_name, context)
        if not self.filesystem.exists(path):
            return []

        items = self.filesystem.iterdir(path)
        return [item for item in items if self.filesystem.is_file(item)]

    def ensure_area_exists(self, area_name: str, context: WorkflowContext) -> Path:
        """Ensure area directory exists, create if needed."""
        path = self.get_area_path(area_name, context)
        self.filesystem.mkdir(path, parents=True, exist_ok=True)
        return path

    def get_archive_path(self, contest_name: str, problem_name: str) -> Path:
        """Get archive path for specific contest/problem."""
        archive_context = WorkflowContext(
            contest_name=contest_name,
            problem_name=problem_name,
            language="dummy"  # Not used in archive path
        )
        return self.get_area_path("archive_area", archive_context)

    def list_archives(self) -> List[tuple[str, str]]:
        """List all available archives as (contest_name, problem_name) tuples."""
        base_path = Path(self.path_vars.get("contest_stock_path", "./contest_stock"))
        archives = []

        if not self.filesystem.exists(base_path):
            return archives

        contest_dirs = self.filesystem.iterdir(base_path)
        for contest_dir in contest_dirs:
            if self.filesystem.is_dir(contest_dir):
                problem_dirs = self.filesystem.iterdir(contest_dir)
                for problem_dir in problem_dirs:
                    if self.filesystem.is_dir(problem_dir):
                        archives.append((contest_dir.name, problem_dir.name))

        return sorted(archives)


def create_folder_mapper_from_env(env_json: Dict[str, Any], language: str, filesystem: FileSystemInterface) -> FolderMapper:
    """Create FolderMapper from env.json configuration."""
    from .config_parser import create_folder_mapper_config

    path_vars = create_folder_mapper_config(env_json, language)
    return FolderMapper(path_vars, filesystem)
