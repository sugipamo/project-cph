"""Path resolution utilities as pure functions"""
from pathlib import Path
import os
from typing import Any, Dict, List
from src.context.resolver.config_resolver import ConfigNode, resolve_best


def get_workspace_path(resolver: ConfigNode, language: str) -> Path:
    """Get workspace path from configuration."""
    node = resolve_best(resolver, [language, "workspace_path"])
    if node is None or node.value is None or node.key != "workspace_path":
        raise TypeError("workspace_pathが設定されていません")
    return Path(node.value)


def get_contest_current_path(resolver: ConfigNode, language: str) -> Path:
    """Get contest current path from configuration."""
    node = resolve_best(resolver, [language, "contest_current_path"])
    if node is None or node.value is None or node.key != "contest_current_path":
        raise TypeError("contest_current_pathが設定されていません")
    return Path(node.value)


def get_contest_env_path() -> Path:
    """Get contest_env path by searching up directory tree."""
    cur = os.path.abspath(os.getcwd())
    while True:
        candidate = os.path.join(cur, "contest_env")
        if os.path.isdir(candidate):
            return Path(candidate)
        parent = os.path.dirname(cur)
        if parent == cur:
            break
        cur = parent
    raise ValueError("contest_env_pathが自動検出できませんでした。contest_envディレクトリが見つかりません。")


def get_contest_template_path(resolver: ConfigNode, language: str) -> Path:
    """Get contest template path from configuration."""
    node = resolve_best(resolver, [language, "contest_template_path"])
    if node is None or node.key != "contest_template_path" or node.value is None:
        raise TypeError("contest_template_pathが設定されていません")
    return Path(node.value)


def get_contest_temp_path(resolver: ConfigNode, language: str) -> Path:
    """Get contest temp path from configuration."""
    node = resolve_best(resolver, [language, "contest_temp_path"])
    if node is None or node.key != "contest_temp_path" or node.value is None:
        raise TypeError("contest_temp_pathが設定されていません")
    return Path(node.value)


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
    node = resolve_best(resolver, [language, "source_file_name"])
    if node is None or node.key != "source_file_name" or node.value is None:
        raise ValueError("source_file_nameが設定されていません")
    return str(node.value)