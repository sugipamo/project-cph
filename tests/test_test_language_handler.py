import pytest
from src.environment.test_language_handler import PythonTestHandler, PypyTestHandler, RustTestHandler, HANDLERS
import os
from src.path_manager.unified_path_manager import UnifiedPathManager
from pathlib import Path
from unittest.mock import MagicMock
import subprocess

class DummyCtl:
    def __init__(self):
        self.calls = []
    def exec_in_container(self, container, cmd, realtime=False):
        self.calls.append((container, cmd))
        return True, 'ok', ''

class DummyCtlFail:
    def exec_in_container(self, container, cmd, realtime=False):
        return False, '', 'error'

def test_handlers_mapping():
    assert 'python' in HANDLERS
    assert 'pypy' in HANDLERS
    assert 'rust' in HANDLERS

def test_base_handler_run_notimplemented():
    from src.environment.test_language_handler import TestLanguageHandler
    handler = TestLanguageHandler()
    import pytest
    with pytest.raises(NotImplementedError):
        handler.run(None, None, None, None)

def make_dummy_file(path, content):
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)

def test_python_handler_build_and_run(tmp_path):
    handler = PythonTestHandler()
    # buildは常に成功
    ok, out, err = handler.build(None, None, None)
    assert ok
    # runはrun_and_measureを呼ぶ
    manager = MagicMock()
    manager.run_and_measure.return_value = MagicMock(returncode=0, stdout="out", stderr="err")
    # CompletedProcess型で返す
    manager.exec_in_container = MagicMock(return_value=subprocess.CompletedProcess(args=[], returncode=0, stdout="out", stderr="err"))
    in_file = tmp_path / "in.txt"
    make_dummy_file(in_file, "input")
    result = handler.run(manager, "name", str(in_file), "main.py", host_in_file=str(in_file))
    assert result[0]
    assert result[1] == "out"
    assert result[2] == "err"

def test_pypy_handler_build_and_run(tmp_path):
    handler = PypyTestHandler()
    ok, out, err = handler.build(None, None, None)
    assert ok
    manager = MagicMock()
    manager.run_and_measure.return_value = MagicMock(returncode=0, stdout="out", stderr="err")
    manager.exec_in_container = MagicMock(return_value=subprocess.CompletedProcess(args=[], returncode=0, stdout="out", stderr="err"))
    in_file = tmp_path / "in.txt"
    make_dummy_file(in_file, "input")
    result = handler.run(manager, "name", str(in_file), "main.py", host_in_file=str(in_file))
    assert result[0]
    assert result[1] == "out"
    assert result[2] == "err"

def test_rust_handler_build_and_run(tmp_path):
    handler = RustTestHandler()
    # build
    manager = MagicMock()
    manager.run_and_measure.return_value = MagicMock(returncode=0, stdout="out", stderr="err")
    manager.exec_in_container = MagicMock(return_value=subprocess.CompletedProcess(args=[], returncode=0, stdout="out2", stderr="err2"))
    src_dir = tmp_path / "rust"
    src_dir.mkdir()
    ok, out, err = handler.build(manager, "name", str(src_dir))
    assert ok
    assert manager.run_and_measure.called
    # run
    bin_dir = src_dir / "target" / "release"
    bin_dir.mkdir(parents=True)
    bin_path = bin_dir / "rust"
    bin_path.write_text("")
    in_file = tmp_path / "in.txt"
    make_dummy_file(in_file, "input")
    manager.run_and_measure.reset_mock()
    manager.run_and_measure.return_value = MagicMock(returncode=0, stdout="out2", stderr="err2")
    result = handler.run(manager, "name", str(in_file), str(src_dir), host_in_file=str(in_file))
    assert result[0]
    assert result[1] == "out2"
    assert result[2] == "err2"

def test_python_handler_run_fail(tmp_path):
    handler = PythonTestHandler()
    manager = MagicMock()
    manager.run_and_measure.return_value = MagicMock(returncode=1, stdout="", stderr="err")
    manager.exec_in_container = MagicMock(return_value=subprocess.CompletedProcess(args=[], returncode=1, stdout="", stderr="err"))
    in_file = tmp_path / "in.txt"
    make_dummy_file(in_file, "input")
    result = handler.run(manager, "name", str(in_file), "main.py", host_in_file=str(in_file))
    assert not result[0]
    assert result[2] == "err"

def test_rust_handler_run_fail(tmp_path):
    handler = RustTestHandler()
    manager = MagicMock()
    manager.run_and_measure.return_value = MagicMock(returncode=1, stdout="", stderr="err")
    manager.exec_in_container = MagicMock(return_value=subprocess.CompletedProcess(args=[], returncode=1, stdout="", stderr="err"))
    src_dir = tmp_path / "rust"
    src_dir.mkdir()
    bin_dir = src_dir / "target" / "release"
    bin_dir.mkdir(parents=True)
    bin_path = bin_dir / "rust"
    bin_path.write_text("")
    in_file = tmp_path / "in.txt"
    make_dummy_file(in_file, "input")
    result = handler.run(manager, "name", str(in_file), str(src_dir), host_in_file=str(in_file))
    assert not result[0]
    assert result[2] == "err"