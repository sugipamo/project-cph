import os
import shutil
import tempfile
import json
from pathlib import Path
from src.contest_file_manager import ContestFileManager
from src.file_operator import MockFileOperator
import pytest

def test_get_exclude_files(tmp_path):
    op = MockFileOperator(base_dir=tmp_path)
    manager = ContestFileManager(op)
    config_path = tmp_path / "config.json"
    config_path.write_text(json.dumps({"moveignore": ["^.*\\.log$", "^debug.*"]}), encoding="utf-8")
    patterns = manager.get_exclude_files(config_path)
    assert patterns == ["^.*\\.log$", "^debug.*"]
    # configがなければ空リスト
    patterns2 = manager.get_exclude_files(tmp_path / "no_config.json")
    assert patterns2 == []

def test_is_ignored():
    op = MockFileOperator()
    manager = ContestFileManager(op)
    # 先頭アンカー付きでテスト
    assert manager._is_ignored("foo.log", [r"^.*\.log$"])
    assert not manager._is_ignored("foo.txt", [r"^.*\.log$"])

def test_remove_empty_parents(tmp_path):
    op = MockFileOperator(base_dir=tmp_path)
    manager = ContestFileManager(op)
    # tmp_path/a/b/c/d を作成
    d = tmp_path / "a" / "b" / "c" / "d"
    d.mkdir(parents=True)
    # dを削除し、c, bも空なら削除、aは残す
    manager._remove_empty_parents(d, tmp_path / "a")
    assert not (tmp_path / "a" / "b").exists()
    assert (tmp_path / "a").exists()

def test_get_exclude_files2(tmp_path):
    op = MockFileOperator()
    manager = ContestFileManager(op)
    config_path = tmp_path / "config.json"
    config_path.write_text(json.dumps({"moveignore": [r"^debug.*"]}))
    excludes = manager.get_exclude_files(config_path)
    assert r"^debug.*" in excludes

def test_resolve_path():
    op = MockFileOperator()
    manager = ContestFileManager(op)
    p = manager.file_operator.resolve_path("foo/bar.txt")
    assert isinstance(p, Path)
    assert str(p).endswith("foo/bar.txt")

def test_get_current_info_and_config_path(tmp_path, monkeypatch):
    op = MockFileOperator()
    manager = ContestFileManager(op)
    monkeypatch.setattr(manager.file_operator, "resolve_path", lambda x=None: tmp_path / (x or ""))
    assert str(manager.get_current_info_path()).endswith("contest_current/system_info.json")
    assert str(manager.get_current_config_path()).endswith("contest_current/config.json") 