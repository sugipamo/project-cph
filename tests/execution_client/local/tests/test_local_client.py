import pytest
from execution_client.local.client import LocalAsyncClient

def test_run_not_implemented():
    client = LocalAsyncClient()
    with pytest.raises(ValueError):
        client.run("test")
    # 正常系: commandを渡すとPopenが返る
    proc = client.run("test2", command=["echo", "hello"])
    assert proc is not None
    assert client.is_running("test2")
    client.stop("test2") 