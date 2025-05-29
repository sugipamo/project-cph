import pytest
from src.env.resource.run.local_run_handler import LocalRunHandler
from src.env.resource.run.docker_run_handler import DockerRunHandler
from src.operations.shell.shell_request import ShellRequest
from src.operations.docker.docker_request import DockerRequest, DockerOpType

class DummyConfig:
    pass
@pytest.fixture
def config():
    return DummyConfig()
def test_localrunhandler_create_process_options(config):
    handler = LocalRunHandler(config)
    cmd = ["echo", "hello"]
    req = handler.create_process_options(cmd)
    assert isinstance(req, ShellRequest)
    assert req.cmd == cmd
def test_dockerrunhandler_create_process_options(config):
    handler = DockerRunHandler(config)
    cmd = ["ls", "-l"]
    req = handler.create_process_options(cmd)
    assert isinstance(req, DockerRequest)
    assert req.op == DockerOpType.EXEC
    assert req.container == "dummy_container"
    assert req.command == "ls -l" 