import unittest.mock

import pytest

from src.operations.requests.python.python_request import PythonRequest
from src.operations.results import OperationResult


class DummyPythonUtils:
    @staticmethod
    def is_script_file(arg):
        return isinstance(arg, (list, tuple)) and len(arg) == 1 and str(arg[0]).endswith(".py")
    @staticmethod
    def run_script_file(path, cwd=None):
        return ("script_out", "", 0)
    @staticmethod
    def run_code_string(code, cwd=None):
        return ("code_out", "", 0)

def test_python_request_repr():
    req = PythonRequest(["print('x')"])
    s = repr(req)
    assert "PythonRequest" in s

def test_python_request_code_string(monkeypatch):
    # Create a mock driver with python_driver attribute
    class MockPythonDriver:
        def is_script_file(self, arg):
            return False
        def run_code_string(self, code, cwd=None):
            return ("ok", "", 0)
    
    class MockUnifiedDriver:
        def __init__(self):
            self.python_driver = MockPythonDriver()
    
    mock_driver = MockUnifiedDriver()
    req = PythonRequest(["print('ok')"])
    result = req._execute_core(mock_driver)
    assert isinstance(result, OperationResult)
    assert result.stdout == "ok"
    assert result.returncode == 0

def test_python_request_script_file(monkeypatch, tmp_path):
    script_path = tmp_path / "test.py"
    script_path.write_text("print('ok')")
    monkeypatch.setattr("src.infrastructure.drivers.python.utils.python_utils.PythonUtils.is_script_file", lambda arg: True)
    monkeypatch.setattr("src.infrastructure.drivers.python.utils.python_utils.PythonUtils.run_script_file", lambda path, cwd=None: ("script", "", 0))
    req = PythonRequest([str(script_path)])
    result = req._execute_core()
    assert result.stdout == "script"
    assert result.returncode == 0

def test_python_request_with_cwd(monkeypatch, tmp_path):
    monkeypatch.setattr("src.infrastructure.drivers.python.utils.python_utils.PythonUtils.is_script_file", lambda arg: False)
    monkeypatch.setattr("src.infrastructure.drivers.python.utils.python_utils.PythonUtils.run_code_string", lambda code, cwd=None: ("cwd", "", 0))
    req = PythonRequest(["print('cwd')"], cwd=str(tmp_path))
    result = req._execute_core()
    assert result.stdout == "cwd"
    assert result.returncode == 0

def test_python_request_execute_exception(monkeypatch):
    monkeypatch.setattr("src.infrastructure.drivers.python.utils.python_utils.PythonUtils.is_script_file", lambda arg: False)
    monkeypatch.setattr("src.infrastructure.drivers.python.utils.python_utils.PythonUtils.run_code_string", lambda code, cwd=None: (_ for _ in ()).throw(Exception("fail")))
    req = PythonRequest(["raise Exception('fail')"])
    result = req._execute_core()
    assert isinstance(result, OperationResult)
    assert result.stderr == "fail"
    assert result.returncode == 1

def test_python_request_code_string_with_patch(monkeypatch):
    with (unittest.mock.patch("src.infrastructure.drivers.python.utils.python_utils.PythonUtils.is_script_file", lambda arg: False),
          unittest.mock.patch("src.infrastructure.drivers.python.utils.python_utils.PythonUtils.run_code_string", lambda code, cwd=None: ("ok", "", 0))):
            req = PythonRequest(["print('ok')"])
            result = req._execute_core()
            assert isinstance(result, OperationResult)
            assert result.stdout == "ok"
            assert result.returncode == 0

def test_python_request_script_file_with_patch(monkeypatch, tmp_path):
    script_path = tmp_path / "test.py"
    script_path.write_text("print('ok')")
    with (unittest.mock.patch("src.infrastructure.drivers.python.utils.python_utils.PythonUtils.is_script_file", lambda arg: True),
          unittest.mock.patch("src.infrastructure.drivers.python.utils.python_utils.PythonUtils.run_script_file", lambda path, cwd=None: ("script", "", 0))):
            req = PythonRequest([str(script_path)])
            result = req._execute_core()
            assert result.stdout == "script"
            assert result.returncode == 0

def test_python_request_with_cwd_with_patch(monkeypatch, tmp_path):
    with (unittest.mock.patch("src.infrastructure.drivers.python.utils.python_utils.PythonUtils.is_script_file", lambda arg: False),
          unittest.mock.patch("src.infrastructure.drivers.python.utils.python_utils.PythonUtils.run_code_string", lambda code, cwd=None: ("cwd", "", 0))):
            req = PythonRequest(["print('cwd')"], cwd=str(tmp_path))
            result = req._execute_core()
            assert result.stdout == "cwd"
            assert result.returncode == 0

def test_python_request_execute_exception_with_patch(monkeypatch):
    with (unittest.mock.patch("src.infrastructure.drivers.python.utils.python_utils.PythonUtils.is_script_file", lambda arg: False),
          unittest.mock.patch("src.infrastructure.drivers.python.utils.python_utils.PythonUtils.run_code_string", lambda code, cwd=None: (_ for _ in ()).throw(Exception("fail")))):
            req = PythonRequest(["raise Exception('fail')"])
            result = req._execute_core()
            assert isinstance(result, OperationResult)
            assert result.stderr == "fail"
            assert result.returncode == 1
