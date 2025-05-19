from abc import ABC, abstractmethod
from typing import List
from src.operations.shell.shell_request import ShellRequest
from src.operations.docker.docker_request import DockerRequest, DockerOpType
from src.operations.shell.shell_driver import ShellDriver
from src.command_registry.env_context import EnvContext


class BaseRunHandler(ABC):
    def __init__(self, config: EnvContext, const_handler):
        self.config = config
        self.const_handler = const_handler

    @abstractmethod
    def create_process_options(self, cmd: list):
        pass

class LocalRunHandler(BaseRunHandler):
    def __init__(self, config: EnvContext, const_handler):
        super().__init__(config, const_handler)
    def create_process_options(self, cmd: list) -> ShellRequest:
        # コマンド配列内の各要素に対して変数展開
        return ShellRequest(cmd)

class DockerRunHandler(BaseRunHandler):
    def __init__(self, config: EnvContext, const_handler):
        super().__init__(config, const_handler)

    def create_process_options(self, cmd: list) -> DockerRequest:
        # DockerRequest(EXEC)を返す
        return DockerRequest(
            DockerOpType.EXEC,
            container=self.const_handler.container_name,
            command=" ".join(cmd),
        )