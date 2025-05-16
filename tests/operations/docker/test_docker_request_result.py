import pytest
from src.operations.docker.docker_request import DockerRequest, DockerOpType
from src.operations.docker.docker_driver import MockDockerDriver
from src.operations.docker.docker_result import DockerResult

def test_dockerrequest_with_mockdriver():
    driver = MockDockerDriver()
    # RUN
    req = DockerRequest(DockerOpType.RUN, image="img", name="c", driver=driver)
    result = req.execute()
    assert result == "mock_container_c"
    # STOP
    req = DockerRequest(DockerOpType.STOP, name="c", driver=driver)
    result = req.execute()
    assert result is None
    # REMOVE
    req = DockerRequest(DockerOpType.REMOVE, name="c", driver=driver)
    result = req.execute()
    assert result is None
    # EXEC
    req = DockerRequest(DockerOpType.EXEC, name="c", command="ls", driver=driver)
    result = req.execute()
    assert result == "mock_exec_result_c_ls"
    # LOGS
    req = DockerRequest(DockerOpType.LOGS, name="c", driver=driver)
    result = req.execute()
    assert result == "mock_logs_c"

def test_dockerresult_methods():
    r = DockerResult(success=True, op="RUN", stdout="ok", stderr="", returncode=0)
    assert r.is_success()
    assert not r.is_failure()
    d = r.to_dict()
    assert d["success"] is True
    assert d["op"] == "RUN"
    # 失敗時
    r2 = DockerResult(success=False, op="RUN", stdout="", stderr="err", returncode=1, exception=None)
    assert not r2.is_success()
    assert r2.is_failure()
    with pytest.raises(RuntimeError):
        r2.raise_if_error()
    # 例外付き
    ex = Exception("fail")
    r3 = DockerResult(success=False, op="RUN", exception=ex)
    with pytest.raises(Exception):
        r3.raise_if_error() 