import pytest
from src.execution_env.request_factory import (
    ShellCommandRequestFactory, DockerCommandRequestFactory, CopyCommandRequestFactory, OjCommandRequestFactory,
    create_requests_from_run_steps
)
from src.execution_env.request_factory_selector import RequestFactorySelector
from src.execution_env.run_step_shell import ShellRunStep
from src.execution_env.run_step_copy import CopyRunStep
from src.execution_env.run_step_oj import OjRunStep
from src.execution_env.run_steps import RunSteps
from src.operations.di_container import DIContainer
from src.operations.docker.docker_request import DockerRequest, DockerOpType
from src.operations.file.file_request import FileRequest, FileOpType
from src.operations.shell.shell_request import ShellRequest

class MockConstHandler:
    def __init__(self):
        self.container_name = "mock_container"
        self.oj_container_name = "mock_oj_container"
    def parse(self, arg):
        return f"parsed_{arg}"

class MockController:
    def __init__(self):
        self.const_handler = MockConstHandler()
        self.env_context = type("EnvContext", (), {"env_type": "local"})()

@pytest.fixture
def di_container():
    di = DIContainer()
    di.register("ShellCommandRequestFactory", lambda: ShellCommandRequestFactory)
    di.register("DockerCommandRequestFactory", lambda: DockerCommandRequestFactory)
    di.register("CopyCommandRequestFactory", lambda: CopyCommandRequestFactory)
    di.register("OjCommandRequestFactory", lambda: OjCommandRequestFactory)
    return di

def test_shell_command_request_factory(di_container):
    controller = MockController()
    step = ShellRunStep(type="shell", cmd=["echo", "hello"])
    factory = RequestFactorySelector.get_factory_for_step(controller, step, di_container)
    req = factory.create_request(step)
    assert isinstance(req, ShellRequest)
    assert req.cmd == ["parsed_echo", "parsed_hello"]

def test_docker_command_request_factory(di_container):
    controller = MockController()
    controller.env_context.env_type = "docker"
    step = ShellRunStep(type="shell", cmd=["ls", "/"])
    factory = RequestFactorySelector.get_factory_for_step(controller, step, di_container)
    req = factory.create_request(step)
    assert isinstance(req, DockerRequest)
    assert req.container == "mock_container"
    assert req.command == "parsed_ls parsed_/"
    assert req.op == DockerOpType.EXEC

def test_copy_command_request_factory(di_container):
    controller = MockController()
    step = CopyRunStep(type="copy", cmd=["src.txt", "dst.txt"])
    factory = RequestFactorySelector.get_factory_for_step(controller, step, di_container)
    req = factory.create_request(step)
    assert isinstance(req, FileRequest)
    assert req.op == FileOpType.COPY
    assert req.path == "parsed_src.txt"
    assert req.dst_path == "parsed_dst.txt"

def test_oj_command_request_factory(di_container):
    controller = MockController()
    step = OjRunStep(type="oj", cmd=["test", "-c", "./main"])
    factory = RequestFactorySelector.get_factory_for_step(controller, step, di_container)
    req = factory.create_request(step)
    assert isinstance(req, DockerRequest)
    assert req.container == "mock_oj_container"
    assert req.command == "parsed_test parsed_-c parsed_./main"
    assert req.op == DockerOpType.EXEC

def test_create_requests_from_run_steps(di_container):
    controller = MockController()
    steps = RunSteps([
        ShellRunStep(type="shell", cmd=["echo", "A"]),
        CopyRunStep(type="copy", cmd=["a.txt", "b.txt"]),
        OjRunStep(type="oj", cmd=["test", "-c", "./main"]),
    ])
    composite = create_requests_from_run_steps(controller, steps, di_container)
    # CompositeRequestのrequestsリストの型・値を確認
    assert len(composite.requests) == 3
    assert isinstance(composite.requests[0], ShellRequest)
    assert isinstance(composite.requests[1], FileRequest)
    assert isinstance(composite.requests[2], DockerRequest)

def test_factory_type_error(di_container):
    controller = MockController()
    step = CopyRunStep(type="copy", cmd=["only_src"])
    factory = RequestFactorySelector.get_factory_for_step(controller, step, di_container)
    with pytest.raises(ValueError):
        factory.create_request(step)

def test_factory_unknown_type(di_container):
    controller = MockController()
    class UnknownStep:
        type = "unknown"
    with pytest.raises(ValueError):
        RequestFactorySelector.get_factory_for_step(controller, UnknownStep(), di_container) 