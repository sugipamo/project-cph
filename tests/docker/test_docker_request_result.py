import pytest

from src.domain.requests.docker.docker_request import DockerOpType, DockerRequest
from src.domain.results.result import OperationResult
from src.infrastructure.mock.mock_docker_driver import MockDockerDriver


def test_dockerrequest_with_mockdriver():
    driver = MockDockerDriver()
    # RUN
    req = DockerRequest(DockerOpType.RUN, image="img", container="c")
    result = req.execute(driver=driver)
    assert "Started container c from img" in result.stdout
    # STOP
    req = DockerRequest(DockerOpType.STOP, container="c")
    result = req.execute(driver=driver)
    assert "Stopped container c" in result.stdout
    # REMOVE
    req = DockerRequest(DockerOpType.REMOVE, container="c")
    result = req.execute(driver=driver)
    assert "Removed container c" in result.stdout
    # EXEC
    req = DockerRequest(DockerOpType.EXEC, container="c", command="ls")
    result = req.execute(driver=driver)
    assert "Executed 'ls' in c" in result.stdout
    # LOGS
    req = DockerRequest(DockerOpType.LOGS, container="c")
    result = req.execute(driver=driver)
    assert result.stdout == "Mock logs for c"

def test_dockerresult_methods():
    r = OperationResult(success=True, op="RUN", stdout="ok", stderr="", returncode=0)
    assert r.is_success()
    assert not r.is_failure()
    d = r.to_dict()
    assert d["success"] is True
    assert d["op"] == "RUN"
    # 失敗時
    r2 = OperationResult(success=False, op="RUN", stdout="", stderr="err", returncode=1, exception=None)
    assert not r2.is_success()
    assert r2.is_failure()
    with pytest.raises(RuntimeError):
        r2.raise_if_error()
    # 例外付き
    ex = Exception("fail")
    r3 = OperationResult(success=False, op="RUN", exception=ex)
    with pytest.raises(Exception):
        r3.raise_if_error()

def test_dockerrequest_no_driver():
    req = DockerRequest(DockerOpType.RUN, image="img", container="c")
    with pytest.raises(ValueError) as excinfo:
        req.execute(None)
    assert "requires a driver" in str(excinfo.value)
