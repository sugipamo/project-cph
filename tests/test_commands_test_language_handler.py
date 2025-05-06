import pytest
from src.environment.test_language_handler import RustTestHandler

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
    ctl = DummyCtlFail()
    handler = RustTestHandler()
    ok, out, err = handler.run(ctl, 'cont', 'input.txt', 'main.rs')
    assert not ok
    assert 'error' in err 