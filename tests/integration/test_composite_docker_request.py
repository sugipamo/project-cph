import pytest
from src.operations.composite_request import CompositeRequest
from src.operations.docker.docker_request import DockerRequest, DockerOpType


def test_composite_request_docker_no_driver():
    req = DockerRequest(DockerOpType.RUN, image="img", container="c")
    composite = CompositeRequest([req])
    with pytest.raises(ValueError) as excinfo:
        composite.execute(driver=None)
    assert str(excinfo.value) == "DockerRequest.execute()にはdriverが必須です"


def test_docker_request_no_driver_direct():
    req = DockerRequest(DockerOpType.RUN, image="img", container="c")
    with pytest.raises(ValueError) as excinfo:
        req.execute(driver=None)
    assert str(excinfo.value) == "DockerRequest.execute()にはdriverが必須です"


@pytest.mark.parametrize("op", [
    DockerOpType.RUN,
    DockerOpType.STOP,
    DockerOpType.REMOVE,
    DockerOpType.EXEC,
    DockerOpType.LOGS,
])
def test_docker_request_no_driver_all_ops(op):
    req = DockerRequest(op, image="img", container="c", command="ls" if op == DockerOpType.EXEC else None)
    with pytest.raises(ValueError) as excinfo:
        req.execute(driver=None)
    assert str(excinfo.value) == "DockerRequest.execute()にはdriverが必須です"


def test_docker_request_no_driver_debug():
    req = DockerRequest(DockerOpType.RUN, image="img", container="c")
    try:
        result = req.execute(driver=None)
        print("RETURNED:", result)
    except Exception as exc:
        print("RAISED:", exc)
        raise
    assert False, "ValueErrorがraiseされるべきです" 