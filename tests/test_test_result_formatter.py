import os
import tempfile
from src.commands.test_result_formatter import ResultFormatter

def test_color_text():
    text = "abc"
    assert ResultFormatter.color_text(text, "red").startswith("\033[31m")
    assert ResultFormatter.color_text(text, "green").startswith("\033[32m")
    assert ResultFormatter.color_text(text, "yellow").startswith("\033[33m")
    assert ResultFormatter.color_text(text, "reset").endswith("\033[0m")

def make_result(name, returncode, stdout, stderr, expected, time=0.123, in_file=None):
    r = {
        "name": name,
        "result": (returncode, stdout, stderr),
        "expected": expected,
        "time": time
    }
    if in_file:
        r["in_file"] = in_file
    return r

def test_format_ac():
    r = make_result("case1", 0, "ok", "", "ok")
    fmt = ResultFormatter(r).format()
    assert "AC" in fmt
    assert "0.123秒" in fmt

def test_format_wa():
    r = make_result("case2", 0, "ng", "", "ok")
    fmt = ResultFormatter(r).format()
    assert "WA" in fmt

def test_format_re():
    r = make_result("case3", 1, "", "", "ok")
    fmt = ResultFormatter(r).format()
    assert "RE" in fmt

def test_format_error_and_stderr():
    r = make_result("case4", 0, "ok", "error happened", "ok")
    fmt = ResultFormatter(r).format()
    assert "error happened" in fmt
    assert "-" * 17 in fmt

def test_format_input(tmp_path):
    in_file = tmp_path / "input.txt"
    in_file.write_text("42\n")
    r = make_result("case5", 0, "42", "", "42", in_file=str(in_file))
    fmt = ResultFormatter(r).format()
    assert "42" in fmt 