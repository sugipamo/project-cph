import os
import tempfile
from pathlib import Path
from unittest.mock import Mock

import pytest

from src.configuration.config_manager import TypeSafeConfigNodeManager
from src.infrastructure.drivers.python.utils.python_utils import PythonUtils


@pytest.fixture
def mock_config_manager():
    """Create a mock configuration manager."""
    mock_config = Mock(spec=TypeSafeConfigNodeManager)

    # Mock the configuration values
    def mock_resolve_config(path, value_type):
        if path == ['python_config', 'interpreters', 'default']:
            return 'python3'
        if path == ['python_config', 'interpreters', 'alternatives']:
            return ['python3', 'python']
        if path == ['python_config', 'error_handling']:
            return {}
        raise KeyError(f"Configuration path not found: {path}")

    mock_config.resolve_config.side_effect = mock_resolve_config
    return mock_config


@pytest.fixture
def python_utils(mock_config_manager):
    """Create a PythonUtils instance for testing."""
    return PythonUtils(mock_config_manager)


def test_is_script_file_true_false(tmp_path, python_utils):
    # ファイルが存在する場合True
    f = tmp_path / "a.py"
    f.write_text("print('ok')")
    assert python_utils.is_script_file([str(f)])
    # ファイルが存在しない場合False
    assert not python_utils.is_script_file(["notfound.py"])
    # 複数要素の場合False
    assert not python_utils.is_script_file(["a.py", "b.py"])

def test_run_script_file(tmp_path, python_utils):
    f = tmp_path / "b.py"
    f.write_text("print('hello')")
    out, err, code = python_utils.run_script_file(str(f), cwd=None)
    assert "hello" in out
    assert code == 0

def test_run_code_string_success(python_utils):
    out, err, code = python_utils.run_code_string("print('abc')", cwd=None)
    assert out.strip() == "abc"
    assert err == ""
    assert code == 0

def test_run_code_string_exception(python_utils):
    out, err, code = python_utils.run_code_string("raise Exception('fail')", cwd=None)
    assert "Exception" in err
    assert code == 1
