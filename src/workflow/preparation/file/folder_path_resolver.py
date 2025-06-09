"""Pure functions for folder path resolution and area management."""
from dataclasses import dataclass
from pathlib import Path
from typing import Dict

from ..core.state_definitions import WorkflowContext


@dataclass
class FolderArea:
    """Definition of a folder area."""
    name: str
    path_template: str
    purpose: str
    description: str


def resolve_folder_path(
    path_template: str,
    context: WorkflowContext,
    path_vars: Dict[str, str]
) -> Path:
    """Resolve a folder path template using context and variables.

    Args:
        path_template: Template string with placeholders
        context: Workflow context containing contest/problem/language info
        path_vars: Additional path variables from configuration

    Returns:
        Resolved Path object
    """
    all_vars = {**path_vars}
    if context.contest_name:
        all_vars["contest_name"] = context.contest_name
    if context.problem_name:
        all_vars["problem_name"] = context.problem_name
    if context.language:
        all_vars["language"] = context.language
        all_vars["language_name"] = context.language

    resolved_path = path_template.format(**all_vars)
    return Path(resolved_path)


def define_standard_areas() -> Dict[str, FolderArea]:
    """Define the standard folder areas.

    Returns:
        Dictionary mapping area names to FolderArea instances
    """
    return {
        "working_area": FolderArea(
            name="working_area",
            path_template="{contest_current_path}",
            purpose="active_work",
            description="Current active problem work"
        ),
        "archive_area": FolderArea(
            name="archive_area",
            path_template="{contest_stock_path}/{contest_name}/{problem_name}",
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


def get_area_path(
    area_name: str,
    areas: Dict[str, FolderArea],
    context: WorkflowContext,
    path_vars: Dict[str, str]
) -> Path:
    """Get the resolved path for a specific area.

    Args:
        area_name: Name of the area to resolve
        areas: Dictionary of available areas
        context: Workflow context
        path_vars: Path variables from configuration

    Returns:
        Resolved Path object

    Raises:
        ValueError: If area_name is not found in areas
    """
    if area_name not in areas:
        raise ValueError(f"Unknown area: {area_name}")

    area = areas[area_name]
    return resolve_folder_path(area.path_template, context, path_vars)
