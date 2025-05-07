import os
import pytest
from src.path_manager.project_path_manager import ProjectPathManager

def test_contest_current():
    pm = ProjectPathManager("/tmp/proj")
    assert pm.contest_current() == os.path.join("/tmp/proj", "contest_current")
    assert pm.contest_current("info.json") == os.path.join("/tmp/proj", "contest_current", "info.json")

def test_contest_stocks():
    pm = ProjectPathManager("/tmp/proj")
    assert pm.contest_stocks() == os.path.join("/tmp/proj", "contest_stocks")
    assert pm.contest_stocks("abc123") == os.path.join("/tmp/proj", "contest_stocks", "abc123")
    assert pm.contest_stocks("abc123", "a") == os.path.join("/tmp/proj", "contest_stocks", "abc123", "a")
    assert pm.contest_stocks("abc123", "a", "python") == os.path.join("/tmp/proj", "contest_stocks", "abc123", "a", "python")
    assert pm.contest_stocks("abc123", "a", "python", "main.py") == os.path.join("/tmp/proj", "contest_stocks", "abc123", "a", "python", "main.py")

def test_contest_env():
    pm = ProjectPathManager("/tmp/proj")
    assert pm.contest_env("python.Dockerfile") == os.path.join("/tmp/proj", "contest_env", "python.Dockerfile")

def test_contest_template():
    pm = ProjectPathManager("/tmp/proj")
    assert pm.contest_template() == os.path.join("/tmp/proj", "contest_template")
    assert pm.contest_template("python") == os.path.join("/tmp/proj", "contest_template", "python")
    assert pm.contest_template("python", "main.py") == os.path.join("/tmp/proj", "contest_template", "python", "main.py")

def test_shortcuts():
    pm = ProjectPathManager("/tmp/proj")
    assert pm.info_json() == os.path.join("/tmp/proj", "contest_current", "info.json")
    assert pm.config_json() == os.path.join("/tmp/proj", "contest_current", "config.json")
    assert pm.test_dir() == os.path.join("/tmp/proj", "contest_current", "test")
    assert pm.readme_md() == os.path.join("/tmp/proj", "contest_current", "README.md") 