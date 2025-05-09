import pytest
from src.environment.test_language_handler import PythonTestHandler, PypyTestHandler, RustTestHandler, HANDLERS
import os
from src.path_manager.unified_path_manager import UnifiedPathManager
from pathlib import Path

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