import pytest
import pytest_asyncio
from src.commands import CommandParser
import src.commands as commands
import json
import os

def test_parse_prints_args():
    parser = CommandParser()
    parser.parse(["abc300", "open", "a", "python"])
    assert parser.parsed == {
        "contest_name": "abc300",
        "command": "open",
        "problem_name": "a",
        "language_name": "python"
    }

def test_parse_with_aliases():
    parser = CommandParser()
    parser.parse(["arc100", "o", "b", "rs"])
    assert parser.parsed == {
        "contest_name": "arc100",
        "command": "open",
        "problem_name": "b",
        "language_name": "rust"
    }

def test_parse_order_independence():
    parser = CommandParser()
    parser.parse(["t", "python", "agc001", "c"])
    assert parser.parsed == {
        "contest_name": "agc001",
        "command": "test",
        "problem_name": "c",
        "language_name": "python"
    }

def test_parse_missing_elements_warns(capsys):
    parser = CommandParser()
    parser.parse(["abc300", "a"])  # command, language_name不足
    assert parser.parsed["contest_name"] == "abc300"
    assert parser.parsed["problem_name"] == "a"
    assert parser.parsed["command"] is None
    assert parser.parsed["language_name"] is None

def test_parse_with_pypy_alias():
    parser = CommandParser()
    parser.parse(["ahc100", "submit", "ex", "py"])
    assert parser.parsed == {
        "contest_name": "ahc100",
        "command": "submit",
        "problem_name": "ex",
        "language_name": "pypy"
    }

@pytest.mark.asyncio
async def test_login():
    with pytest.raises(NotImplementedError):
        await commands.login()

@pytest.mark.asyncio
async def test_open_problem():
    with pytest.raises(NotImplementedError):
        await commands.open_problem("abc300", "a", "python")

@pytest.mark.asyncio
async def test_test_problem():
    with pytest.raises(NotImplementedError):
        await commands.test_problem("abc300", "a", "python")

@pytest.mark.asyncio
async def test_submit_problem():
    with pytest.raises(NotImplementedError):
        await commands.submit_problem("abc300", "a", "python")

def test_get_effective_args_with_infojson(tmp_path):
    # info.jsonを用意
    info = {"contest_name": "abc300", "problem_name": "a", "language_name": "python"}
    info_path = tmp_path / "info.json"
    with open(info_path, "w", encoding="utf-8") as f:
        json.dump(info, f)
    parser = CommandParser()
    parser.parse(["open", "python", "a"])
    args = parser.get_effective_args(str(info_path))
    assert args["contest_name"] == "abc300"
    assert args["problem_name"] == "a"
    assert args["language_name"] == "python"
    assert args["command"] == "open" 
    