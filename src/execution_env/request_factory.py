from src.operations.shell.shell_request import ShellRequest
from src.operations.file.file_request import FileRequest, FileOpType
from src.operations.composite_request import CompositeRequest
from src.operations.docker.docker_request import DockerRequest, DockerOpType
from src.execution_env.run_step import ShellRunStep, CopyRunStep, OjRunStep
from src.operations.di_container import DIContainer

# 抽象基底ファクトリ
class BaseCommandRequestFactory:
    def __init__(self, controller):
        self.controller = controller

    def create_request(self, run_step):
        raise NotImplementedError

# shell用（local環境）
class ShellCommandRequestFactory(BaseCommandRequestFactory):
    def create_request(self, run_step):
        if not isinstance(run_step, ShellRunStep):
            raise TypeError(f"ShellCommandRequestFactory expects ShellRunStep, got {type(run_step).__name__}")
        cmd = [self.controller.const_handler.parse(arg) for arg in run_step.cmd]
        return ShellRequest(cmd)

# shell用（docker環境）
class DockerCommandRequestFactory(BaseCommandRequestFactory):
    def create_request(self, run_step):
        if not isinstance(run_step, ShellRunStep):
            raise TypeError(f"DockerCommandRequestFactory expects ShellRunStep, got {type(run_step).__name__}")
        cmd = [self.controller.const_handler.parse(arg) for arg in run_step.cmd]
        container_name = self.controller.const_handler.container_name
        return DockerRequest(
            DockerOpType.EXEC,
            container=container_name,
            command=" ".join(cmd)
        )

# copy用
class CopyCommandRequestFactory(BaseCommandRequestFactory):
    def create_request(self, run_step):
        if not isinstance(run_step, CopyRunStep):
            raise TypeError(f"CopyCommandRequestFactory expects CopyRunStep, got {type(run_step).__name__}")
        if len(run_step.cmd) < 2:
            raise ValueError("CopyRunStep: cmdにはsrcとdstの2つが必要です")
        src = self.controller.const_handler.parse(run_step.cmd[0])
        dst = self.controller.const_handler.parse(run_step.cmd[1])
        return FileRequest(FileOpType.COPY, src, dst_path=dst)

# type→factoryクラスのマッピング
FACTORY_MAP = {
    "shell": ShellCommandRequestFactory,
    "docker_shell": DockerCommandRequestFactory,
    "copy": CopyCommandRequestFactory,
    "oj": None,
    "test": None,
}

def get_shell_factory(controller, di_container: DIContainer):
    env_type = getattr(controller.env_context, "env_type", "local")
    if env_type.lower() == "docker":
        return di_container.resolve("DockerCommandRequestFactory")(controller)
    else:
        return di_container.resolve("ShellCommandRequestFactory")(controller)

class OjCommandRequestFactory(BaseCommandRequestFactory):
    def create_request(self, run_step):
        if not isinstance(run_step, OjRunStep):
            raise TypeError(f"OjCommandRequestFactory expects OjRunStep, got {type(run_step).__name__}")
        if not run_step.cmd:
            raise ValueError("OjRunStep: cmdは必須です")
        cmd = [self.controller.const_handler.parse(arg) for arg in run_step.cmd]
        container_name = self.controller.const_handler.oj_container_name
        return DockerRequest(
            DockerOpType.EXEC,
            container=container_name,
            command=" ".join(cmd)
        )

def get_factory_for_step(controller, step, di_container: DIContainer):
    # step: RunStep型を想定
    if isinstance(step, ShellRunStep):
        return get_shell_factory(controller, di_container)
    elif isinstance(step, CopyRunStep):
        return di_container.resolve("CopyCommandRequestFactory")(controller)
    elif isinstance(step, OjRunStep):
        return di_container.resolve("OjCommandRequestFactory")(controller)
    else:
        factory_cls = FACTORY_MAP.get(getattr(step, "type", None))
        if not factory_cls:
            raise ValueError(f"Unknown or unsupported run type: {getattr(step, 'type', None)} (step={step})")
        return di_container.resolve(factory_cls.__name__)(controller)

def create_requests_from_run_steps(controller, run_steps, di_container: DIContainer):
    """
    run_steps: RunSteps型（RunStepのリスト）
    controller: EnvResourceController
    di_container: DIContainer
    """
    requests = []
    for step in run_steps:
        factory = get_factory_for_step(controller, step, di_container)
        req = factory.create_request(step)
        requests.append(req)
    return CompositeRequest.make_composite_request(requests) 