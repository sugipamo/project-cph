import os
from pathlib import Path
import pytest
from src.path_manager.project_path_manager import ProjectPathManager

def test_contest_current():
    pm = ProjectPathManager("/tmp/proj")
    assert pm.contest_current() == Path("/tmp/proj") / "contest_current"
    assert pm.contest_current("system_info.json") == Path("/tmp/proj") / "contest_current" / "system_info.json"

def test_contest_stocks():
    pm = ProjectPathManager("/tmp/proj")
    assert pm.contest_stocks() == Path("/tmp/proj") / "contest_stocks"
    assert pm.contest_stocks("abc123") == Path("/tmp/proj") / "contest_stocks" / "abc123"
    assert pm.contest_stocks("abc123", "a") == Path("/tmp/proj") / "contest_stocks" / "abc123" / "a"
    assert pm.contest_stocks("abc123", "a", "python") == Path("/tmp/proj") / "contest_stocks" / "abc123" / "a" / "python"
    assert pm.contest_stocks("abc123", "a", "python", "main.py") == Path("/tmp/proj") / "contest_stocks" / "abc123" / "a" / "python" / "main.py"

def test_contest_env():
    pm = ProjectPathManager("/tmp/proj")
    assert pm.contest_env("python.Dockerfile") == Path("/tmp/proj") / "contest_env" / "python.Dockerfile"

def test_contest_template():
    pm = ProjectPathManager("/tmp/proj")
    assert pm.contest_template() == Path("/tmp/proj") / "contest_template"
    assert pm.contest_template("python") == Path("/tmp/proj") / "contest_template" / "python"
    assert pm.contest_template("python", "main.py") == Path("/tmp/proj") / "contest_template" / "python" / "main.py"

def test_shortcuts():
    pm = ProjectPathManager("/tmp/proj")
    assert pm.info_json() == Path("/tmp/proj") / "contest_current" / "system_info.json"
    assert pm.config_json() == Path("/tmp/proj") / "contest_current" / "config.json"
    assert pm.test_dir() == Path("/tmp/proj") / "contest_current" / "test"
    assert pm.readme_md() == Path("/tmp/proj") / "contest_current" / "README.md" 