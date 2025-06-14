"""Configuration-based path resolution functions.
Migrated from src/operations/utils/path_utils.py
"""
import os
from pathlib import Path

from src.context.resolver.config_resolver import ConfigNode, resolve_best


def get_workspace_path(resolver: ConfigNode, language: str) -> Path:
    """Get workspace path from configuration."""
    # Try multiple resolution paths to find workspace_path
    for path in [[language, "paths", "workspace_path"], [language, "workspace_path"], ["shared", "paths", "workspace_path"], ["workspace_path"]]:
        config_node = resolve_best(resolver, path)
        if config_node is not None and config_node.value is not None and config_node.key == "workspace_path":
            return Path(config_node.value)
    raise TypeError("workspace_pathが設定されていません")


def get_contest_current_path(resolver: ConfigNode, language: str) -> Path:
    """Get contest current path from configuration."""
    # Try multiple resolution paths to find contest_current_path
    for path in [[language, "paths", "contest_current_path"], [language, "contest_current_path"], ["shared", "paths", "contest_current_path"], ["contest_current_path"]]:
        config_node = resolve_best(resolver, path)
        if config_node is not None and config_node.value is not None and config_node.key == "contest_current_path":
            return Path(config_node.value)
    raise TypeError("contest_current_pathが設定されていません")


def get_contest_env_path() -> Path:
    """Get contest_env path by searching up directory tree."""
    current_dir = os.path.abspath(os.getcwd())
    while True:
        candidate_path = os.path.join(current_dir, "contest_env")
        if os.path.isdir(candidate_path):
            return Path(candidate_path)
        parent_dir = os.path.dirname(current_dir)
        if parent_dir == current_dir:
            break
        current_dir = parent_dir
    raise ValueError("contest_env_pathが自動検出できませんでした。contest_envディレクトリが見つかりません。")


def get_contest_template_path(resolver: ConfigNode, language: str) -> Path:
    """Get contest template path from configuration."""
    # Try multiple resolution paths to find contest_template_path
    for path in [[language, "paths", "contest_template_path"], [language, "contest_template_path"], ["shared", "paths", "contest_template_path"], ["contest_template_path"]]:
        config_node = resolve_best(resolver, path)
        if config_node is not None and config_node.value is not None and config_node.key == "contest_template_path":
            return Path(config_node.value)
    raise TypeError("contest_template_pathが設定されていません")


def get_contest_temp_path(resolver: ConfigNode, language: str) -> Path:
    """Get contest temp path from configuration."""
    # Try multiple resolution paths to find contest_temp_path
    for path in [[language, "paths", "contest_temp_path"], [language, "contest_temp_path"], ["shared", "paths", "contest_temp_path"], ["contest_temp_path"]]:
        config_node = resolve_best(resolver, path)
        if config_node is not None and config_node.value is not None and config_node.key == "contest_temp_path":
            return Path(config_node.value)
    raise TypeError("contest_temp_pathが設定されていません")


def get_test_case_path(contest_current_path: Path) -> Path:
    """Get test case directory path."""
    return contest_current_path / "test"


def get_test_case_in_path(contest_current_path: Path) -> Path:
    """Get test case input directory path."""
    return get_test_case_path(contest_current_path) / "in"


def get_test_case_out_path(contest_current_path: Path) -> Path:
    """Get test case output directory path."""
    return get_test_case_path(contest_current_path) / "out"


def get_source_file_name(resolver: ConfigNode, language: str) -> str:
    """Get source file name from configuration using resolve."""
    # Try multiple resolution paths to find source_file_name
    for path in [[language, "source_file_name"], ["shared", "source_file_name"], ["source_file_name"]]:
        config_node = resolve_best(resolver, path)
        if config_node is not None and config_node.value is not None and config_node.key == "source_file_name":
            return str(config_node.value)
    raise ValueError("source_file_nameが設定されていません")
