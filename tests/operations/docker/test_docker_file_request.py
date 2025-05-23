import pytest
from src.operations.docker.docker_file_request import DockerFileRequest
from src.operations.mock.mock_docker_driver import MockDockerDriver


def test_docker_file_request_to_container():
    class DummyDockerFileRequest(DockerFileRequest):
        @property
        def operation_type(self):
            from src.operations.constants.operation_type import OperationType
            return OperationType.DOCKER
    mock_driver = MockDockerDriver()
    req = DummyDockerFileRequest(
        src_path="host.txt",
        dst_path="/container/path.txt",
        container="test_container",
        to_container=True
    )
    result = req.execute(driver=mock_driver)
    assert result.is_success()
    assert result.op == "DOCKER_CP"
    assert mock_driver.operations[-1][:4] == ("cp", "host.txt", "/container/path.txt", "test_container")
    assert mock_driver.operations[-1][4] is True

def test_docker_file_request_from_container():
    class DummyDockerFileRequest(DockerFileRequest):
        @property
        def operation_type(self):
            from src.operations.constants.operation_type import OperationType
            return OperationType.DOCKER
    mock_driver = MockDockerDriver()
    req = DummyDockerFileRequest(
        src_path="/container/path.txt",
        dst_path="host.txt",
        container="test_container",
        to_container=False
    )
    result = req.execute(driver=mock_driver)
    assert result.is_success()
    assert result.op == "DOCKER_CP"
    assert mock_driver.operations[-1][:4] == ("cp", "/container/path.txt", "host.txt", "test_container")
    assert mock_driver.operations[-1][4] is False

def test_docker_file_request_no_driver():
    class DummyDockerFileRequest(DockerFileRequest):
        @property
        def operation_type(self):
            from src.operations.constants.operation_type import OperationType
            return OperationType.DOCKER
    req = DummyDockerFileRequest(
        src_path="a",
        dst_path="b",
        container="c1",
        to_container="c2"
    )
    with pytest.raises(ValueError):
        req.execute(None) 