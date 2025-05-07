import pytest
from src.environment.test_language_handler import RustTestHandler
from src.unified_path_manager import UnifiedPathManager
import os

class DummyCtl:
    def exec_in_container(self, container, cmd, realtime=False):
        return True, 'ok', ''

class DummyCtlFail:
    def exec_in_container(self, container, cmd, realtime=False):
        return False, '', 'error'

def test_rust_handler_build_fail():
    ctl = DummyCtlFail()
    handler = RustTestHandler()
    ok, out, err = handler.build(ctl, 'cont', 'main.rs')
    assert not ok
    assert 'error' in err

def test_rust_handler_run_fail():
    handler = RustTestHandler()
    import src.environment.test_language_handler as tlh
    # テスト用upmを差し替え、to_container_pathが必ず絶対パスを返すようにする
    class DummyUPM:
        def to_container_path(self, path):
            return os.path.abspath(path)
    tlh.upm = DummyUPM()
    ctl = DummyCtlFail()
    ok, out, err = handler.run(ctl, 'cont', 'input.txt', 'main.rs')
    assert not ok
    assert 'error' in err 