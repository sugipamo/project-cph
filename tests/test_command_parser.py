import pytest
from unittest.mock import patch, MagicMock
from src.command_parser import CommandParser

@pytest.mark.parametrize("args,expected", [
    (["abc123", "test", "a", "python", "docker"],
     {"contest_name": "abc123", "command": "test", "problem_name": "a", "language_name": "python", "exec_mode": "docker"}),
    (["arc", "submit", "b", "pypy"],
     {"contest_name": "arc", "command": "submit", "problem_name": "b", "language_name": "pypy", "exec_mode": None}),
    (["agc", "open", "ex", "rust", "local"],
     {"contest_name": "agc", "command": "open", "problem_name": "ex", "language_name": "rust", "exec_mode": "local"}),
    (["ahc", "login"],
     {"contest_name": "ahc", "command": "login", "problem_name": None, "language_name": None, "exec_mode": None}),
    (["abc", "t", "a", "python"],
     {"contest_name": "abc", "command": "test", "problem_name": "a", "language_name": "python", "exec_mode": None}),
])
def test_command_parser_parse(args, expected):
    parser = CommandParser()
    parser.parse(args)
    for k, v in expected.items():
        assert parser.parsed[k] == v

@patch("src.command_parser.InfoJsonManager")
def test_get_effective_args_with_infojson(mock_info):
    parser = CommandParser()
    parser.parse(["abc", "test", "a", "python"])
    # 全部埋まってる場合はinfojson参照しない
    mock_info.return_value.data = {"contest_name": "zzz", "problem_name": "y", "language_name": "x", "exec_mode": "docker"}
    result = parser.get_effective_args("dummy.json")
    assert result["contest_name"] == "abc"
    # 一部Noneならinfojsonから補完
    parser = CommandParser()
    parser.parse(["abc", "test"])
    mock_info.return_value.data = {"problem_name": "a", "language_name": "python", "exec_mode": "docker"}
    result = parser.get_effective_args("dummy.json")
    assert result["problem_name"] == "a"
    assert result["language_name"] == "python"
    assert result["exec_mode"] == "docker"

@patch("src.command_parser.InfoJsonManager")
def test_get_effective_args_infojson_exception(mock_info):
    parser = CommandParser()
    parser.parse(["abc", "test"])
    mock_info.side_effect = Exception("file not found")
    # 例外が出ても落ちない
    result = parser.get_effective_args("dummy.json")
    assert result["contest_name"] == "abc"
    assert result["problem_name"] is None
    assert result["language_name"] is None
    assert result["exec_mode"] is None 