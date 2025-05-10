import os
import tempfile
import json
import pytest
from src.file.info_json_manager import InfoJsonManager

def test_load_and_save(tmp_path):
    path = tmp_path / "system_info.json"
    # 保存
    manager = InfoJsonManager(str(path))
    manager.data = {"foo": 1}
    manager.save()
    # 再ロード
    manager2 = InfoJsonManager(str(path))
    assert manager2.data["foo"] == 1
    assert "__comment" in manager2.data
    assert manager2.data["__comment"].startswith("通常、このファイルを編集する必要はありません")

def test_get_and_update_containers(tmp_path):
    path = tmp_path / "system_info.json"
    manager = InfoJsonManager(str(path))
    containers = [
        {"name": "c1", "type": "test", "language": "python"},
        {"name": "c2", "type": "ojtools"},
        {"name": "c3", "type": "test", "language": "rust"},
    ]
    manager.update_containers(containers)
    # 全件
    assert len(manager.get_containers()) == 3
    # typeフィルタ
    assert len(manager.get_containers(type="test")) == 2
    # languageフィルタ
    assert len(manager.get_containers(language="python")) == 1
    # type+language
    assert manager.get_containers(type="test", language="rust")[0]["name"] == "c3"

def test_validate_warns_on_duplicate_names(tmp_path, capsys):
    path = tmp_path / "system_info.json"
    manager = InfoJsonManager(str(path))
    containers = [
        {"name": "dup", "type": "test"},
        {"name": "dup", "type": "ojtools"},
    ]
    manager.update_containers(containers)
    manager.validate()
    captured = capsys.readouterr()
    assert "重複" in captured.out

def test_load_nonexistent_file(tmp_path):
    path = tmp_path / "notfound.json"
    manager = InfoJsonManager(str(path))
    assert manager.data == {} 