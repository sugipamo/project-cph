import os
import tempfile
import json
import pytest
from src.config_json_manager import ConfigJsonManager

def test_load_and_save():
    with tempfile.TemporaryDirectory() as tmpdir:
        path = os.path.join(tmpdir, "config.json")
        manager = ConfigJsonManager(path)
        manager.data = {"foo": "bar"}
        manager.save()
        # ファイルができているか
        assert os.path.exists(path)
        # loadで内容が復元されるか
        manager2 = ConfigJsonManager(path)
        assert manager2.data == {"foo": "bar"}

def test_get_and_set_language_id():
    with tempfile.TemporaryDirectory() as tmpdir:
        path = os.path.join(tmpdir, "config.json")
        manager = ConfigJsonManager(path)
        assert manager.get_language_id() == {}
        manager.set_language_id({"py": "python3"})
        assert manager.get_language_id() == {"py": "python3"}

def test_ensure_language_id():
    with tempfile.TemporaryDirectory() as tmpdir:
        path = os.path.join(tmpdir, "config.json")
        manager = ConfigJsonManager(path)
        manager.ensure_language_id({"cpp": "g++"})
        assert manager.get_language_id() == {"cpp": "g++"}
        # 2回目は上書きしない
        manager.ensure_language_id({"py": "python3"})
        assert manager.get_language_id() == {"cpp": "g++"}

def test_get_and_set_entry_file():
    with tempfile.TemporaryDirectory() as tmpdir:
        path = os.path.join(tmpdir, "config.json")
        manager = ConfigJsonManager(path)
        assert manager.get_entry_file() == {}
        manager.set_entry_file("python", "main.py")
        assert manager.get_entry_file("python") == "main.py"
        assert manager.get_entry_file() == {"python": "main.py"}

def test_get_moveignore():
    with tempfile.TemporaryDirectory() as tmpdir:
        path = os.path.join(tmpdir, "config.json")
        manager = ConfigJsonManager(path)
        assert manager.get_moveignore() == []
        manager.data["moveignore"] = [".git", "__pycache__"]
        manager.save()
        manager2 = ConfigJsonManager(path)
        assert manager2.get_moveignore() == [".git", "__pycache__"] 