import pytest
from src.operations.composite_request import CompositeRequest
from src.operations.shell.shell_request import ShellRequest

def test_composite_request_shell_no_driver():
    req = ShellRequest(["echo", "hello"])
    composite = CompositeRequest([req])
    with pytest.raises(ValueError) as excinfo:
        composite.execute(None)
    assert str(excinfo.value) == "ShellRequest.execute()にはdriverが必須です" 