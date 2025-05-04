import os
import shutil
import tempfile
import json
from pathlib import Path
from src.contest_file_manager import ContestFileManager
from src.file_operator import MockFileOperator

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
    patterns = ["^.*\\.log$", "^debug.*"]
    assert manager._is_ignored("foo.log", patterns)
    assert manager._is_ignored("debug123", patterns)
    assert not manager._is_ignored("main.py", patterns)

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