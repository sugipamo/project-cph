import pytest
from src.execution_client.dummy import DummyExecutionClient

def test_run_not_implemented():
    client = DummyExecutionClient()
    with pytest.raises(NotImplementedError):
        client.run("test") 