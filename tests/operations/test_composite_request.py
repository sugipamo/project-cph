import pytest
from src.operations.composite_request import CompositeRequest, flatten_results
from src.operations.shell.shell_request import ShellRequest
from src.operations.result import OperationResult
from src.operations.file.file_request import FileRequest, FileOpType
from src.operations.operation_type import OperationType

def test_composite_request_shell_and_file():
    req1 = ShellRequest(["echo", "foo"])
    req2 = ShellRequest(["echo", "bar"])
    req3 = FileRequest(FileOpType.WRITE, "/tmp/test_composite.txt", content="baz")
    composite = CompositeRequest([req1, req2, req3])
    results = composite.execute()
    assert len(results) == 3
    assert results[0].operation_type == OperationType.SHELL
    assert results[1].operation_type == OperationType.SHELL
    assert results[2].operation_type == OperationType.FILE
    assert "foo" in results[0].stdout or results[0].stdout == ""
    assert "bar" in results[1].stdout or results[1].stdout == ""
    assert results[2].success

def test_composite_request_nested_flatten():
    req1 = ShellRequest(["echo", "foo"])
    req2 = ShellRequest(["echo", "bar"])
    inner = CompositeRequest([req1, req2])
    req3 = FileRequest(FileOpType.WRITE, "/tmp/test_composite2.txt", content="baz")
    outer = CompositeRequest([inner, req3])
    results = outer.execute()
    flat = flatten_results(results)
    assert len(flat) == 3
    assert any(r.operation_type == OperationType.SHELL and "foo" in r.stdout for r in flat)
    assert any(r.operation_type == OperationType.SHELL and "bar" in r.stdout for r in flat)
    assert any(r.operation_type == OperationType.FILE and r.success for r in flat) 