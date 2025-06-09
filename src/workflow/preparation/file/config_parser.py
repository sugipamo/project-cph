"""Pure functions for configuration parsing and path variable extraction."""
from typing import Any, Dict


def create_folder_mapper_config(
    env_json: Dict[str, Any],
    language: str
) -> Dict[str, str]:
    """Create path variables configuration for folder mapping.

    Args:
        env_json: Environment configuration dictionary
        language: Programming language name

    Returns:
        Dictionary of path variables for folder mapping
    """
    path_vars = {}

    # Get language-specific configuration
    lang_config = env_json.get("languages", {}).get(language, {}).get("paths", {})

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

    return path_vars
