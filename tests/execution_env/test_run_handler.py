import pytest
from src.execution_env.resource_handler.run_handler import LocalRunHandler, DockerRunHandler
from src.operations.shell.shell_request import ShellRequest
from src.operations.docker.docker_request import DockerRequest, DockerOpType

class DummyConstHandler:
    @property
    def container_name(self):
        return "dummy_container"

class DummyDriver:
    pass

def test_local_run_handler_create_process_options():
    config = {}
    const_handler = DummyConstHandler()
    handler = LocalRunHandler(config, const_handler)
    cmd = ["echo", "hello"]
    driver = DummyDriver()
    req = handler.create_process_options(cmd, driver=driver)
    assert isinstance(req, ShellRequest)
    assert req.cmd == cmd
    assert req.driver == driver

def test_docker_run_handler_create_process_options():
    config = {}
    const_handler = DummyConstHandler()
    handler = DockerRunHandler(config, const_handler)
    cmd = ["ls", "/workspace"]
    driver = DummyDriver()
    req = handler.create_process_options(cmd, driver=driver)
    assert isinstance(req, DockerRequest)
    assert req.op == DockerOpType.EXEC
    assert req.name == "dummy_container"
    assert req.command == "ls /workspace"
    assert req._driver == driver 