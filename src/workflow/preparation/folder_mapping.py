"""Folder mapping system for state transitions."""
import os
from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import dataclass

from .state_definitions import WorkflowContext


@dataclass
class FolderArea:
    """Definition of a folder area."""
    name: str
    path_template: str
    purpose: str
    description: str
    
    def resolve_path(self, context: WorkflowContext, path_vars: Dict[str, str]) -> Path:
        """Resolve the actual path using context and variables."""
        # Combine context and path variables
        all_vars = {**path_vars}
        if context.contest_name:
            all_vars["contest_name"] = context.contest_name
        if context.problem_id:
            all_vars["problem_id"] = context.problem_id
        if context.language:
            all_vars["language"] = context.language
            all_vars["language_name"] = context.language
        
        # Format the path template
        resolved_path = self.path_template.format(**all_vars)
        return Path(resolved_path)


class FolderMapper:
    """Maps logical areas to physical folder structures."""
    
    def __init__(self, path_vars: Dict[str, str]):
        """Initialize with path variables from env.json."""
        self.path_vars = path_vars
        self._areas = self._define_areas()
    
    def _define_areas(self) -> Dict[str, FolderArea]:
        """Define the standard folder areas."""
        return {
            "working_area": FolderArea(
                name="working_area",
                path_template="{contest_current_path}",
                purpose="active_work", 
                description="Current active problem work"
            ),
            "archive_area": FolderArea(
                name="archive_area",
                path_template="{contest_stock_path}/{contest_name}/{problem_id}",
                purpose="completed_work_storage",
                description="Archived completed work"
            ),
            "template_area": FolderArea(
                name="template_area", 
                path_template="{contest_template_path}/{language}",
                purpose="clean_starting_files",
                description="Template files for new problems"
            ),
            "workspace_area": FolderArea(
                name="workspace_area",
                path_template="{workspace_path}",
                purpose="temporary_execution", 
                description="Temporary execution workspace"
            )
        }
    
    def get_area_path(self, area_name: str, context: WorkflowContext) -> Path:
        """Get the resolved path for an area."""
        if area_name not in self._areas:
            raise ValueError(f"Unknown area: {area_name}")
        
        area = self._areas[area_name]
        return area.resolve_path(context, self.path_vars)
    
    def area_exists(self, area_name: str, context: WorkflowContext) -> bool:
        """Check if area path exists."""
        path = self.get_area_path(area_name, context)
        return path.exists()
    
    def area_has_files(self, area_name: str, context: WorkflowContext) -> bool:
        """Check if area has any files."""
        path = self.get_area_path(area_name, context)
        if not path.exists():
            return False
        
        try:
            # Check if directory has any files (not just subdirectories)
            for item in path.iterdir():
                if item.is_file():
                    return True
            return False
        except (OSError, PermissionError):
            return False
    
    def list_area_files(self, area_name: str, context: WorkflowContext) -> List[Path]:
        """List all files in an area."""
        path = self.get_area_path(area_name, context)
        if not path.exists():
            return []
        
        try:
            return [item for item in path.iterdir() if item.is_file()]
        except (OSError, PermissionError):
            return []
    
    def ensure_area_exists(self, area_name: str, context: WorkflowContext) -> Path:
        """Ensure area directory exists, create if needed."""
        path = self.get_area_path(area_name, context)
        path.mkdir(parents=True, exist_ok=True)
        return path
    
    def get_archive_path(self, contest_name: str, problem_id: str) -> Path:
        """Get archive path for specific contest/problem."""
        archive_context = WorkflowContext(
            contest_name=contest_name,
            problem_id=problem_id,
            language="dummy"  # Not used in archive path
        )
        return self.get_area_path("archive_area", archive_context)
    
    def list_archives(self) -> List[tuple[str, str]]:
        """List all available archives as (contest_name, problem_id) tuples."""
        base_path = Path(self.path_vars.get("contest_stock_path", "./contest_stock"))
        archives = []
        
        if not base_path.exists():
            return archives
        
        try:
            for contest_dir in base_path.iterdir():
                if contest_dir.is_dir():
                    for problem_dir in contest_dir.iterdir():
                        if problem_dir.is_dir():
                            archives.append((contest_dir.name, problem_dir.name))
        except (OSError, PermissionError):
            pass
        
        return sorted(archives)


def create_folder_mapper_from_env(env_json: Dict[str, Any], language: str) -> FolderMapper:
    """Create FolderMapper from env.json configuration."""
    if language not in env_json:
        raise ValueError(f"Language {language} not found in env.json")
    
    lang_config = env_json[language]
    
    # Extract path variables
    path_vars = {}
    
    # Language-specific paths
    for key in ["contest_current_path", "contest_stock_path", "contest_template_path", "workspace_path"]:
        if key in lang_config:
            path_vars[key] = lang_config[key]
    
    # Shared paths (fallback)
    if "shared" in env_json and "paths" in env_json["shared"]:
        shared_paths = env_json["shared"]["paths"]
        for key, value in shared_paths.items():
            if key not in path_vars:
                path_vars[key] = value
    
    return FolderMapper(path_vars)