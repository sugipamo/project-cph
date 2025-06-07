import os
import tempfile
from pathlib import Path

import pytest

from src.infrastructure.drivers.python.utils.python_utils import PythonUtils


def test_is_script_file_true_false(tmp_path):
    # ファイルが存在する場合True
    f = tmp_path / "a.py"
    f.write_text("print('ok')")
    assert PythonUtils.is_script_file([str(f)])
    # ファイルが存在しない場合False
    assert not PythonUtils.is_script_file(["notfound.py"])
    # 複数要素の場合False
    assert not PythonUtils.is_script_file(["a.py", "b.py"])

def test_run_script_file(tmp_path):
    f = tmp_path / "b.py"
    f.write_text("print('hello')")
    out, err, code = PythonUtils.run_script_file(str(f))
    assert "hello" in out
    assert code == 0

def test_run_code_string_success():
    out, err, code = PythonUtils.run_code_string("print('abc')")
    assert out.strip() == "abc"
    assert err == ""
    assert code == 0

def test_run_code_string_exception():
    out, err, code = PythonUtils.run_code_string("raise Exception('fail')")
    assert "Exception" in err
    assert code == 1
