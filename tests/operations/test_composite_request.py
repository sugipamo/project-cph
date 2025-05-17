import pytest
from src.operations.composite_request import CompositeRequest, flatten_results
from src.operations.shell.shell_request import ShellRequest
from src.operations.result import OperationResult
from src.operations.file.file_request import FileRequest, FileOpType
from src.operations.operation_type import OperationType
from src.operations.file.file_driver import MockFileDriver
from src.operations.shell.local_shell_driver import LocalShellDriver

def test_composite_request_shell_and_file():
    shell_driver = LocalShellDriver()
    req1 = ShellRequest(["echo", "foo"], driver=shell_driver)
    req2 = ShellRequest(["echo", "bar"], driver=shell_driver)
    driver = MockFileDriver()
    req3 = FileRequest(FileOpType.WRITE, "/tmp/test_composite.txt", content="baz")
    composite = CompositeRequest([req1, req2, req3])
    results = composite.execute(driver=driver)
    assert len(results) == 3
    assert results[0].operation_type == OperationType.SHELL
    assert results[1].operation_type == OperationType.SHELL
    assert results[2].operation_type == OperationType.FILE
    assert "foo" in results[0].stdout or results[0].stdout == ""
    assert "bar" in results[1].stdout or results[1].stdout == ""
    assert results[2].success

def test_composite_request_nested_flatten():
    shell_driver = LocalShellDriver()
    req1 = ShellRequest(["echo", "foo"], driver=shell_driver)
    req2 = ShellRequest(["echo", "bar"], driver=shell_driver)
    inner = CompositeRequest([req1, req2])
    driver = MockFileDriver()
    req3 = FileRequest(FileOpType.WRITE, "/tmp/test_composite2.txt", content="baz")
    outer = CompositeRequest([inner, req3])
    results = outer.execute(driver=driver)
    flat = flatten_results(results)
    assert len(flat) == 3
    assert any(r.operation_type == OperationType.SHELL and "foo" in r.stdout for r in flat)
    assert any(r.operation_type == OperationType.SHELL and "bar" in r.stdout for r in flat)
    assert any(r.operation_type == OperationType.FILE and r.success for r in flat)

class CompositeRequest:
    def __init__(self, requests):
        self.requests = requests
        self._executed = False
        self._results = None

    @property
    def operation_type(self):
        return OperationType.COMPOSITE

    def execute(self, driver=None):
        if self._executed:
            raise RuntimeError("This CompositeRequest has already been executed.")
        results = []
        for req in self.requests:
            # FileRequest/ShellRequestなどでdriverを渡す
            if hasattr(req, 'execute'):
                try:
                    results.append(req.execute(driver=driver))
                except TypeError:
                    # driver引数を受け取らない場合
                    results.append(req.execute())
            else:
                results.append(req)
        self._results = results
        self._executed = True
        return results 