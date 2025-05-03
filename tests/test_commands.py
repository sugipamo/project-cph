import pytest
from src.commands import CommandParser

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
    captured = capsys.readouterr()
    assert "警告: commandが特定できませんでした。" in captured.out
    assert "警告: language_nameが特定できませんでした。" in captured.out

def test_parse_with_pypy_alias():
    parser = CommandParser()
    parser.parse(["ahc100", "submit", "ex", "py"])
    assert parser.parsed == {
        "contest_name": "ahc100",
        "command": "submit",
        "problem_name": "ex",
        "language_name": "pypy"
    } 
    