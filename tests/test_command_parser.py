import os
import json
import pytest
from src.command_parser import CommandParser

def test_parse_args_basic():
    parser = CommandParser()
    parser.parse(["abc300", "open", "a", "python"])
    args = parser.get_effective_args()
    assert args["contest_name"] == "abc300"
    assert args["command"] == "open"
    assert args["problem_name"] == "a"
    assert args["language_name"] == "python"

def test_parse_args_aliases():
    parser = CommandParser()
    parser.parse(["abc300", "o", "b", "py"])
    args = parser.get_effective_args()
    assert args["command"] == "open"
    assert args["language_name"] == "pypy"

def test_parse_args_order_independent():
    parser = CommandParser()
    parser.parse(["python", "a", "open", "abc300"])
    args = parser.get_effective_args()
    assert args["contest_name"] == "abc300"
    assert args["command"] == "open"
    assert args["problem_name"] == "a"
    assert args["language_name"] == "python"

def test_parse_args_missing(tmp_path):
    parser = CommandParser()
    parser.parse(["abc300", "open"])
    # 存在しないsystem_info.jsonを指定して補完を無効化
    args = parser.get_effective_args(info_json_path=str(tmp_path / "nosystem_info.json"))
    assert args["problem_name"] is None
    assert args["language_name"] is None

def test_parse_args_invalid():
    parser = CommandParser()
    parser.parse(["abc300", "invalidcmd", "a", "python"])
    args = parser.get_effective_args()
    assert args["command"] is None

def test_parse_partial(monkeypatch, tmp_path):
    # CONTEST_NAMESとLANGUAGESをテスト用に限定
    monkeypatch.setattr("src.command_parser.CONTEST_NAMES", ["abc", "def"])
    monkeypatch.setattr("src.command_parser.LANGUAGES", {"python": {"aliases": ["python3"]}})
    parser = CommandParser()
    parser.parse(["zzz999", "a"])
    # 存在しないsystem_info.jsonを指定して補完を無効化
    args = parser.get_effective_args(info_json_path=str(tmp_path / "nosystem_info.json"))
    assert args["contest_name"] is None
    assert args["problem_name"] == "a"
    assert args["command"] is None
    assert args["language_name"] is None

def test_get_effective_args_infojson(tmp_path):
    # system_info.jsonを用意
    info = {"contest_name": "abc999", "problem_name": "b", "language_name": "rust"}
    info_path = tmp_path / "system_info.json"
    info_path.write_text(json.dumps(info), encoding="utf-8")
    parser = CommandParser()
    parser.parse(["open"])
    args = parser.get_effective_args(info_json_path=str(info_path))
    assert args["contest_name"] == "abc999"
    assert args["problem_name"] == "b"
    assert args["language_name"] == "rust"
    assert args["command"] == "open"

def test_get_effective_args_infojson_missing(tmp_path):
    parser = CommandParser()
    parser.parse(["open"])
    # 存在しないsystem_info.jsonを指定して補完を無効化
    args = parser.get_effective_args(info_json_path=str(tmp_path / "nosystem_info.json"))
    assert args["contest_name"] is None
    assert args["problem_name"] is None
    assert args["language_name"] is None
    assert args["command"] == "open"

def test_parse_invalid(monkeypatch, tmp_path):
    monkeypatch.setattr("src.command_parser.CONTEST_NAMES", ["abc", "def"])
    monkeypatch.setattr("src.command_parser.LANGUAGES", {"python": {"aliases": ["python3"]}})
    parser = CommandParser()
    parser.parse(["foo", "bar"])
    args = parser.get_effective_args(info_json_path=str(tmp_path / "nosystem_info.json"))
    assert args["contest_name"] is None
    assert args["problem_name"] is None
    assert args["language_name"] is None
    assert args["command"] is None 