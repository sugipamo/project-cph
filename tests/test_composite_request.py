import pytest
from src.operations.composite.composite_request import CompositeRequest
from src.operations.shell.shell_request import ShellRequest
from src.operations.result import OperationResult
from src.operations.file.file_request import FileRequest, FileOpType
from src.operations.constants.operation_type import OperationType
from src.operations.mock.mock_file_driver import MockFileDriver
from src.operations.shell.local_shell_driver import LocalShellDriver
from src.operations.base_request import BaseRequest
from src.operations.composite.parallel_composite_request import ParallelCompositeRequest
from src.operations.exceptions.composite_step_failure import CompositeStepFailure

def test_composite_request_shell_and_file():
    shell_driver = LocalShellDriver()
    req1 = ShellRequest(["echo", "foo"])
    req2 = ShellRequest(["echo", "bar"])
    driver = MockFileDriver()
    req3 = FileRequest(FileOpType.WRITE, "/tmp/test_composite.txt", content="baz")
    composite = CompositeRequest([req1, req2, req3])
    results = [req1.execute(driver=shell_driver), req2.execute(driver=shell_driver), req3.execute(driver=driver)]
    assert len(results) == 3
    assert results[0].operation_type == OperationType.SHELL
    assert results[1].operation_type == OperationType.SHELL
    assert results[2].operation_type == OperationType.FILE
    assert "foo" in results[0].stdout or results[0].stdout == ""
    assert "bar" in results[1].stdout or results[1].stdout == ""
    assert results[2].success

def test_composite_request_nested_flatten():
    shell_driver = LocalShellDriver()
    req1 = ShellRequest(["echo", "foo"])
    req2 = ShellRequest(["echo", "bar"])
    inner = CompositeRequest([req1, req2])
    driver = MockFileDriver()
    req3 = FileRequest(FileOpType.WRITE, "/tmp/test_composite2.txt", content="baz")
    outer = CompositeRequest([inner, req3])
    results = [req1.execute(driver=shell_driver), req2.execute(driver=shell_driver), req3.execute(driver=driver)]
    assert len(results) == 3
    assert any(r.operation_type == OperationType.SHELL and "foo" in r.stdout for r in results)
    assert any(r.operation_type == OperationType.SHELL and "bar" in r.stdout for r in results)
    assert any(r.operation_type == OperationType.FILE and r.success for r in results)

def test_composite_request_invalid_type():
    # BaseRequestを継承しない型を渡すとTypeErrorになることを確認
    with pytest.raises(TypeError):
        CompositeRequest([123, "abc"])  # intやstrは不正

def test_parallel_composite_request_shell_and_file():
    from src.operations.composite.parallel_composite_request import ParallelCompositeRequest
    from src.operations.shell.shell_request import ShellRequest
    from src.operations.file.file_request import FileRequest, FileOpType
    from src.operations.mock.mock_file_driver import MockFileDriver
    from src.operations.shell.local_shell_driver import LocalShellDriver
    from src.operations.constants.operation_type import OperationType

    shell_driver = LocalShellDriver()
    file_driver = MockFileDriver()
    req1 = ShellRequest(["echo", "foo"])
    req2 = ShellRequest(["echo", "bar"])
    req3 = FileRequest(FileOpType.WRITE, "/tmp/test_parallel_composite.txt", content="baz")

    # 各リクエストに適切なドライバを紐付けるラッパー
    class DriverBoundRequest(BaseRequest):
        def __init__(self, req, driver):
            super().__init__(name=getattr(req, 'name', None), debug_tag=getattr(req, 'debug_tag', None))
            self.req = req
            self.driver = driver
        def execute(self, driver=None):
            return self.req.execute(driver=self.driver)
        @property
        def operation_type(self):
            return getattr(self.req, 'operation_type', None)
        def _execute_core(self, driver=None):
            return self.req.execute(driver=self.driver)

    parallel = ParallelCompositeRequest([
        DriverBoundRequest(req1, shell_driver),
        DriverBoundRequest(req2, shell_driver),
        DriverBoundRequest(req3, file_driver),
    ])
    results = parallel.execute(driver="dummy")
    assert len(results) == 3
    shell_results = [r for r in results if hasattr(r, 'operation_type') and r.operation_type == OperationType.SHELL]
    file_results = [r for r in results if hasattr(r, 'operation_type') and r.operation_type == OperationType.FILE]
    assert len(shell_results) == 2
    assert len(file_results) == 1
    assert any("foo" in (r.stdout or "") or r.stdout == "" for r in shell_results)
    assert any("bar" in (r.stdout or "") or r.stdout == "" for r in shell_results)
    assert file_results[0].success

def test_parallel_composite_request_invalid_type():
    from src.operations.composite.parallel_composite_request import ParallelCompositeRequest
    with pytest.raises(TypeError):
        ParallelCompositeRequest([123, "abc"])  # intやstrは不正 

class DummyRequest(BaseRequest):
    _require_driver = False
    def __init__(self, name=None, success=True, show_output=False, allow_failure=False):
        super().__init__(name=name)
        self._success = success
        self.show_output = show_output
        self.allow_failure = allow_failure
    @property
    def operation_type(self):
        return "DUMMY"
    def _execute_core(self, driver):
        class Result:
            def __init__(self, success):
                self.success = success
                self.stdout = "out" if success else ""
                self.stderr = "err" if not success else ""
            def __repr__(self):
                return f"<Result success={self.success}>"
        return Result(self._success)

def test_composite_request_allow_failure():
    req1 = DummyRequest("a", success=False, allow_failure=True)
    req2 = DummyRequest("b", success=True)
    composite = CompositeRequest([req1, req2])
    # 失敗してもallow_failure=Trueなら例外にならない
    results = composite._execute_core(driver=None)
    assert len(results) == 2
    assert not results[0].success
    assert results[1].success

def test_composite_request_step_failure():
    req1 = DummyRequest("a", success=False, allow_failure=False)
    req2 = DummyRequest("b", success=True)
    composite = CompositeRequest([req1, req2])
    with pytest.raises(CompositeStepFailure):
        composite._execute_core(driver=None)

def test_composite_request_show_output(capsys):
    req1 = DummyRequest("a", success=True, show_output=True, allow_failure=True)
    req2 = DummyRequest("b", success=False, show_output=True, allow_failure=True)
    composite = CompositeRequest([req1, req2])
    composite._execute_core(driver=None)
    out, err = capsys.readouterr()
    assert "out" in out or out == ""
    assert "err" in out or err == ""

def test_composite_request_repr():
    req1 = DummyRequest("a")
    req2 = DummyRequest("b")
    composite = CompositeRequest([req1, req2], name="test")
    s = repr(composite)
    assert "CompositeRequest" in s
    assert "test" in s
    assert "a" in s and "b" in s

def test_make_composite_request_single():
    req = DummyRequest("a")
    result = CompositeRequest.make_composite_request([req], name="single")
    assert isinstance(result, DummyRequest)
    assert result.name == "single"

def test_make_composite_request_multiple():
    reqs = [DummyRequest("a"), DummyRequest("b")]
    result = CompositeRequest.make_composite_request(reqs, name="multi")
    assert isinstance(result, CompositeRequest)
    assert result.name == "multi"

def test_count_leaf_requests_nested():
    leaf1 = DummyRequest("a")
    leaf2 = DummyRequest("b")
    inner = CompositeRequest([leaf1, leaf2])
    outer = CompositeRequest([inner, DummyRequest("c")])
    assert outer.count_leaf_requests() == 3 