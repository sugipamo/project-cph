import pytest
from execution_client.dummy.client import DummyExecutionClient

def test_run_not_implemented():
    client = DummyExecutionClient()
    with pytest.raises(NotImplementedError):
        client.run("test") 