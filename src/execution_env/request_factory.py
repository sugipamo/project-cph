from src.operations.shell.shell_request import ShellRequest
from src.operations.file.file_request import FileRequest, FileOpType
from src.operations.composite_request import CompositeRequest
from src.operations.docker.docker_request import DockerRequest, DockerOpType

# 抽象基底ファクトリ
class BaseCommandRequestFactory:
    def __init__(self, controller):
        self.controller = controller

    def create_request(self, run_config: dict):
        raise NotImplementedError

# shell用（local環境）
class ShellCommandRequestFactory(BaseCommandRequestFactory):
    def create_request(self, run_config: dict):
        cmd = [self.controller.const_handler.parse(arg) for arg in run_config["cmd"]]
        return ShellRequest(cmd)

# shell用（docker環境）
class DockerCommandRequestFactory(BaseCommandRequestFactory):
    def create_request(self, run_config: dict):
        cmd = [self.controller.const_handler.parse(arg) for arg in run_config["cmd"]]
        container_name = self.controller.const_handler.container_name
        return DockerRequest(
            DockerOpType.EXEC,
            container=container_name,
            command=" ".join(cmd)
        )

# copy用
class CopyCommandRequestFactory(BaseCommandRequestFactory):
    def create_request(self, run_config: dict):
        src = self.controller.const_handler.parse(run_config["cmd"][0])
        dst = self.controller.const_handler.parse(run_config["cmd"][1])
        return FileRequest(FileOpType.COPY, src, dst_path=dst)

# type→factoryのディスパッチ辞書（shellは特殊化のため一旦外す）
FACTORY_MAP = {
    # "shell": ShellCommandRequestFactory,  # env_typeで分岐するため外す
    "oj": None,
    "test": None,
    "copy": CopyCommandRequestFactory,
}

def get_shell_factory(controller):
    env_type = getattr(controller.env_context, "env_type", "local")
    if env_type.lower() == "docker":
        return DockerCommandRequestFactory(controller)
    else:
        return ShellCommandRequestFactory(controller)

def get_factory_for_step(controller, step):
    if step["type"] == "shell":
        return get_shell_factory(controller)
    factory_cls = FACTORY_MAP.get(step["type"])
    if not factory_cls:
        raise ValueError(f"Unknown run type: {step['type']}")
    return factory_cls(controller)

def create_requests_from_run_steps(controller, run_steps):
    """
    run_steps: env.jsonのrun配列
    controller: EnvResourceController
    """
    requests = []
    for step in run_steps:
        factory = get_factory_for_step(controller, step)
        req = factory.create_request(step)
        requests.append(req)
    return CompositeRequest.make_composite_request(requests) 