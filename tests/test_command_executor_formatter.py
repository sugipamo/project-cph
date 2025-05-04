import pytest
from src.command_executor import TestResultFormatter

def test_ac_format():
    result = {
        "name": "sample-1.in",
        "result": (0, "2\n", ""),
        "time": 0.123,
        "expected": "2\n",
        "in_file": None,
    }
    fmt = TestResultFormatter(result)
    out = fmt.format()
    assert "AC" in out
    assert "sample-1.in" in out
    assert "0.123" in out
    assert "Expected | Output" in out
    assert "2        | 2" in out

def test_wa_format():
    result = {
        "name": "sample-2.in",
        "result": (0, "3\n", ""),
        "time": 0.456,
        "expected": "2\n",
        "in_file": None,
    }
    fmt = TestResultFormatter(result)
    out = fmt.format()
    assert "WA" in out
    assert "Expected | Output" in out
    assert "2        | 3" in out

def test_re_format():
    result = {
        "name": "sample-3.in",
        "result": (1, "", "error occurred"),
        "time": 0.789,
        "expected": "",
        "in_file": None,
    }
    fmt = TestResultFormatter(result)
    out = fmt.format()
    assert "RE" in out
    assert "error occurred" in out
    assert "-" * 17 in out

def test_input_and_error(tmp_path):
    in_file = tmp_path / "input.txt"
    in_file.write_text("1 2 3\n4 5 6\n")
    result = {
        "name": "sample-4.in",
        "result": (1, "", "error!"),
        "time": 1.23,
        "expected": "",
        "in_file": str(in_file),
    }
    fmt = TestResultFormatter(result)
    out = fmt.format()
    assert "1 2 3" in out and "4 5 6" in out
    assert "error!" in out
    assert "RE" in out

def test_table_empty():
    result = {
        "name": "sample-5.in",
        "result": (0, "", ""),
        "time": 0.0,
        "expected": "",
        "in_file": None,
    }
    fmt = TestResultFormatter(result)
    out = fmt.format()
    # テーブルが空でもエラーにならない
    assert isinstance(out, str) 