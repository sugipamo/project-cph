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
    req = PythonRequest(["print('x')"], cwd=None, show_output=True, name=None, debug_tag=None)
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
    req = PythonRequest(["print('ok')"], cwd=None, show_output=True, name=None, debug_tag=None)
    result = req._execute_core(mock_driver)
    assert isinstance(result, OperationResult)
    assert result.stdout == "ok"
    assert result.returncode == 0

def test_python_request_script_file(monkeypatch, tmp_path):
    script_path = tmp_path / "test.py"
    script_path.write_text("print('ok')")

    class MockPythonDriver:
        def is_script_file(self, arg):
            return True
        def run_script_file(self, path, cwd=None):
            return ("script", "", 0)

    class MockUnifiedDriver:
        def __init__(self):
            self.python_driver = MockPythonDriver()

    mock_driver = MockUnifiedDriver()
    req = PythonRequest([str(script_path)], cwd=None, show_output=True, name=None, debug_tag=None)
    result = req._execute_core(mock_driver)
    assert result.stdout == "script"
    assert result.returncode == 0

def test_python_request_with_cwd(monkeypatch, tmp_path):
    class MockPythonDriver:
        def is_script_file(self, arg):
            return False
        def run_code_string(self, code, cwd=None):
            return ("cwd", "", 0)

    class MockUnifiedDriver:
        def __init__(self):
            self.python_driver = MockPythonDriver()

    mock_driver = MockUnifiedDriver()
    req = PythonRequest(["print('cwd')"], cwd=str(tmp_path), show_output=True, name=None, debug_tag=None)
    result = req._execute_core(mock_driver)
    assert result.stdout == "cwd"
    assert result.returncode == 0

def test_python_request_execute_exception(monkeypatch):
    class MockPythonDriver:
        def is_script_file(self, arg):
            return False
        def run_code_string(self, code, cwd=None):
            raise Exception("fail")

    class MockUnifiedDriver:
        def __init__(self):
            self.python_driver = MockPythonDriver()

    mock_driver = MockUnifiedDriver()
    req = PythonRequest(["raise Exception('fail')"], cwd=None, show_output=True, name=None, debug_tag=None)
    result = req._execute_core(mock_driver)
    assert isinstance(result, OperationResult)
    assert result.stderr == "fail"
    assert result.returncode == 1

def test_python_request_code_string_with_patch(monkeypatch):
    # These tests now use mock drivers instead of PythonUtils patches
    class MockPythonDriver:
        def is_script_file(self, arg):
            return False
        def run_code_string(self, code, cwd=None):
            return ("ok", "", 0)

    class MockUnifiedDriver:
        def __init__(self):
            self.python_driver = MockPythonDriver()

    mock_driver = MockUnifiedDriver()
    req = PythonRequest(["print('ok')"], cwd=None, show_output=True, name=None, debug_tag=None)
    result = req._execute_core(mock_driver)
    assert isinstance(result, OperationResult)
    assert result.stdout == "ok"
    assert result.returncode == 0

def test_python_request_script_file_with_patch(monkeypatch, tmp_path):
    script_path = tmp_path / "test.py"
    script_path.write_text("print('ok')")

    class MockPythonDriver:
        def is_script_file(self, arg):
            return True
        def run_script_file(self, path, cwd=None):
            return ("script", "", 0)

    class MockUnifiedDriver:
        def __init__(self):
            self.python_driver = MockPythonDriver()

    mock_driver = MockUnifiedDriver()
    req = PythonRequest([str(script_path)], cwd=None, show_output=True, name=None, debug_tag=None)
    result = req._execute_core(mock_driver)
    assert result.stdout == "script"
    assert result.returncode == 0

def test_python_request_with_cwd_with_patch(monkeypatch, tmp_path):
    class MockPythonDriver:
        def is_script_file(self, arg):
            return False
        def run_code_string(self, code, cwd=None):
            return ("cwd", "", 0)

    class MockUnifiedDriver:
        def __init__(self):
            self.python_driver = MockPythonDriver()

    mock_driver = MockUnifiedDriver()
    req = PythonRequest(["print('cwd')"], cwd=str(tmp_path), show_output=True, name=None, debug_tag=None)
    result = req._execute_core(mock_driver)
    assert result.stdout == "cwd"
    assert result.returncode == 0

def test_python_request_execute_exception_with_patch(monkeypatch):
    class MockPythonDriver:
        def is_script_file(self, arg):
            return False
        def run_code_string(self, code, cwd=None):
            raise Exception("fail")

    class MockUnifiedDriver:
        def __init__(self):
            self.python_driver = MockPythonDriver()

    mock_driver = MockUnifiedDriver()
    req = PythonRequest(["raise Exception('fail')"], cwd=None, show_output=True, name=None, debug_tag=None)
    result = req._execute_core(mock_driver)
    assert isinstance(result, OperationResult)
    assert result.stderr == "fail"
    assert result.returncode == 1
