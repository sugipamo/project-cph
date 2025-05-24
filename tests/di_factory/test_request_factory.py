import pytest
from src.env.step.run_step_shell import ShellRunStep
from src.env.step.run_step_copy import CopyRunStep
from src.env.step.run_step_oj import OjRunStep
from src.env.step.run_steps import RunSteps
from src.env.factory.shell_command_request_factory import ShellCommandRequestFactory
from src.env.factory.docker_command_request_factory import DockerCommandRequestFactory
from src.env.factory.copy_command_request_factory import CopyCommandRequestFactory
from src.env.factory.oj_command_request_factory import OjCommandRequestFactory
from src.env.factory.base_command_request_factory import BaseCommandRequestFactory
from src.env.factory.request_factory_selector import RequestFactorySelector
from src.operations.di_container import DIContainer
from src.operations.docker.docker_request import DockerRequest, DockerOpType
from src.operations.file.file_request import FileRequest, FileOpType
from src.operations.shell.shell_request import ShellRequest
from src.env.factory.request_factory import create_requests_from_run_steps
from src.env.step.run_step_remove import RemoveRunStep
from src.env.factory.remove_command_request_factory import RemoveCommandRequestFactory
from src.env.step.run_step_build import BuildRunStep
from src.env.factory.build_command_request_factory import BuildCommandRequestFactory
from src.env.factory.python_command_request_factory import PythonCommandRequestFactory

class MockConstHandler:
    def __init__(self):
        self.container_name = "mock_container"
        self.oj_container_name = "mock_oj_container"
        self.oj_image_name = "mock_oj_image"
        self.contest_temp_path = "/tmp/mock_contest_temp"
        self.oj_dockerfile_text = "FROM dummy"
    def parse(self, arg):
        return f"parsed_{arg}"

class MockController:
    def __init__(self):
        self.const_handler = MockConstHandler()
        self.env_context = type("EnvContext", (), {"env_type": "local"})()

@pytest.fixture
def operations():
    di = DIContainer()
    di.register("ShellCommandRequestFactory", lambda: ShellCommandRequestFactory)
    di.register("DockerCommandRequestFactory", lambda: DockerCommandRequestFactory)
    di.register("CopyCommandRequestFactory", lambda: CopyCommandRequestFactory)
    di.register("OjCommandRequestFactory", lambda: OjCommandRequestFactory)
    di.register("RemoveCommandRequestFactory", lambda: RemoveCommandRequestFactory)
    di.register("BuildCommandRequestFactory", lambda: BuildCommandRequestFactory)
    di.register("PythonCommandRequestFactory", lambda: PythonCommandRequestFactory)
    di.register("DockerRequest", lambda: DockerRequest)
    di.register("DockerOpType", lambda: DockerOpType)
    di.register("FileRequest", lambda: FileRequest)
    di.register("FileOpType", lambda: FileOpType)
    return di

def test_shell_command_request_factory(operations):
    controller = MockController()
    step = ShellRunStep(type="shell", cmd=["echo", "hello"])
    factory = RequestFactorySelector.get_factory_for_step(controller, step, operations)
    req = factory.create_request(step)
    assert isinstance(req, ShellRequest)
    assert req.cmd == ["parsed_echo", "parsed_hello"]

def test_docker_command_request_factory(operations):
    controller = MockController()
    controller.env_context.env_type = "docker"
    step = ShellRunStep(type="shell", cmd=["ls", "/"])
    factory = RequestFactorySelector.get_factory_for_step(controller, step, operations)
    req = factory.create_request(step)
    assert isinstance(req, DockerRequest)
    assert req.container == "mock_container"
    assert req.command == "parsed_ls parsed_/"
    assert req.op == DockerOpType.EXEC

def test_copy_command_request_factory(operations):
    controller = MockController()
    step = CopyRunStep(type="copy", cmd=["src.txt", "dst.txt"])
    factory = RequestFactorySelector.get_factory_for_step(controller, step, operations)
    req = factory.create_request(step)
    assert isinstance(req, FileRequest)
    assert req.op == FileOpType.COPY
    assert req.path == "parsed_src.txt"
    assert req.dst_path == "parsed_dst.txt"

def test_oj_command_request_factory(operations):
    controller = MockController()
    controller.env_context.env_type = "docker"
    step = OjRunStep(type="oj", cmd=["test", "-c", "./main"])
    factory = RequestFactorySelector.get_factory_for_step(controller, step, operations)
    req = factory.create_request(step)
    assert isinstance(req, DockerRequest)
    assert req.op == DockerOpType.EXEC
    assert req.container == "mock_oj_container"
    assert req.command == "parsed_test parsed_-c parsed_./main"

def test_create_requests_from_run_steps(operations):
    controller = MockController()
    steps = RunSteps([
        ShellRunStep(type="shell", cmd=["echo", "hello"]),
        CopyRunStep(type="copy", cmd=["src.txt", "dst.txt"]),
    ])
    composite = create_requests_from_run_steps(controller, steps, operations)
    assert isinstance(composite, ShellRequest) or hasattr(composite, "requests")

def test_factory_type_error(operations):
    controller = MockController()
    step = CopyRunStep(type="copy", cmd=["only_src"])
    factory = RequestFactorySelector.get_factory_for_step(controller, step, operations)
    with pytest.raises(ValueError):
        factory.create_request(step)

def test_factory_unknown_type(operations):
    controller = MockController()
    class UnknownStep:
        type = "unknown"
    with pytest.raises(KeyError):
        RequestFactorySelector.get_factory_for_step(controller, UnknownStep(), operations)

def test_remove_command_request_factory(operations):
    controller = MockController()
    step = RemoveRunStep(type="remove", cmd=["target.txt"])
    factory = RequestFactorySelector.get_factory_for_step(controller, step, operations)
    req = factory.create_request(step)
    assert isinstance(req, FileRequest)
    assert req.op == FileOpType.REMOVE
    assert req.path == "parsed_target.txt"

def test_build_command_request_factory(operations):
    controller = MockController()
    step = BuildRunStep(type="build", cmd=["make", "all"])
    factory = RequestFactorySelector.get_factory_for_step(controller, step, operations)
    req = factory.create_request(step)
    assert isinstance(req, ShellRequest)
    assert req.cmd == ["make", "all"]
    # cmd省略時のデフォルト
    step2 = BuildRunStep(type="build", cmd=[])
    req2 = factory.create_request(step2)
    assert isinstance(req2, ShellRequest)
    # デフォルトは["make"]
    assert req2.cmd == ["make"] 