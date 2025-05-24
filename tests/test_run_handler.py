import pytest
from src.env.resource.run.run_handler import LocalRunHandler, DockerRunHandler
from src.operations.shell.shell_request import ShellRequest
from src.operations.docker.docker_request import DockerRequest, DockerOpType

class DummyConstHandler:
    container_name = "cont"
class DummyConfig:
    pass
@pytest.fixture
def const_handler():
    return DummyConstHandler()
@pytest.fixture
def config():
    return DummyConfig()
def test_localrunhandler_create_process_options(config, const_handler):
    handler = LocalRunHandler(config, const_handler)
    cmd = ["echo", "hello"]
    req = handler.create_process_options(cmd)
    assert isinstance(req, ShellRequest)
    assert req.cmd == cmd
def test_dockerrunhandler_create_process_options(config, const_handler):
    handler = DockerRunHandler(config, const_handler)
    cmd = ["ls", "-l"]
    req = handler.create_process_options(cmd)
    assert isinstance(req, DockerRequest)
    assert req.op == DockerOpType.EXEC
    assert req.container == "cont"
    assert req.command == "ls -l" 