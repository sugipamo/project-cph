import pytest
from src.environment.test_language_handler import PythonTestHandler, PypyTestHandler, RustTestHandler, HANDLERS
import os

class DummyCtl:
    def __init__(self):
        self.calls = []
    def exec_in_container(self, container, cmd):
        self.calls.append((container, cmd))
        return True, 'ok', ''

def test_python_handler_run():
    ctl = DummyCtl()
    handler = PythonTestHandler()
    ok, out, err = handler.run(ctl, 'cont', 'input.txt', 'main.py')
    assert ok and out == 'ok'
    assert ctl.calls[0][1][0] == 'sh'
    assert 'python3' in ctl.calls[0][1][-1]

def test_pypy_handler_run():
    ctl = DummyCtl()
    handler = PypyTestHandler()
    ok, out, err = handler.run(ctl, 'cont', 'input.txt', 'main.py')
    assert ok and out == 'ok'
    assert 'pypy3' in ctl.calls[0][1][-1]

def test_rust_handler_build_and_run(tmp_path):
    from src.environment import test_language_handler
    ctl = DummyCtl()
    handler = RustTestHandler()
    # テスト用path_mapperを差し替え
    handler.path_mapper = test_language_handler.DockerPathMapper(str(tmp_path), '/workspace')
    test_language_handler.path_mapper = handler.path_mapper
    # .temp/a.outをtmp_path配下に作成
    abs_out = os.path.join(tmp_path, '.temp/a.out')
    os.makedirs(os.path.dirname(abs_out), exist_ok=True)
    with open(abs_out, 'w') as f:
        f.write('dummy')
    ok, out, err = handler.build(ctl, 'cont', os.path.join(tmp_path, 'main.rs'))
    assert ok and out == 'ok'
    assert 'rustc' in ctl.calls[0][1]
    ok, out, err = handler.run(ctl, 'cont', '/workspace/input.txt', os.path.join(tmp_path, 'main.rs'))
    assert ok and out == 'ok'
    assert '/workspace/.temp/a.out' in ctl.calls[-1][1][-1]

def test_handlers_mapping():
    assert isinstance(HANDLERS['python'], PythonTestHandler)
    assert isinstance(HANDLERS['pypy'], PypyTestHandler)
    assert isinstance(HANDLERS['rust'], RustTestHandler)

def test_base_handler_run_notimplemented():
    from src.environment.test_language_handler import TestLanguageHandler
    handler = TestLanguageHandler()
    import pytest
    with pytest.raises(NotImplementedError):
        handler.run(None, None, None, None)

def test_python_handler_run_exception():
    from src.environment.test_language_handler import PythonTestHandler
    class DummyCtl:
        def exec_in_container(self, container, cmd):
            raise RuntimeError("fail")
    handler = PythonTestHandler()
    with pytest.raises(RuntimeError):
        handler.run(DummyCtl(), 'cont', 'input.txt', 'main.py')

def test_pypy_handler_run_exception():
    from src.environment.test_language_handler import PypyTestHandler
    class DummyCtl:
        def exec_in_container(self, container, cmd):
            raise RuntimeError("fail")
    handler = PypyTestHandler()
    with pytest.raises(RuntimeError):
        handler.run(DummyCtl(), 'cont', 'input.txt', 'main.py')

def test_rust_handler_build_and_run_exception():
    from src.environment.test_language_handler import RustTestHandler
    class DummyCtl:
        def exec_in_container(self, container, cmd):
            raise RuntimeError("fail")
    handler = RustTestHandler()
    with pytest.raises(RuntimeError):
        handler.build(DummyCtl(), 'cont', 'main.rs')
    with pytest.raises(RuntimeError):
        handler.run(DummyCtl(), 'cont', 'input.txt', 'main.rs') 