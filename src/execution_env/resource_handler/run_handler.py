from abc import ABC, abstractmethod
from typing import List
from src.operations.shell.shell_request import ShellRequest
from src.operations.docker.docker_request import DockerRequest, DockerOpType


class BaseRunHandler(ABC):
    def __init__(self, config: dict, const_handler):
        self.config = config
        self.const_handler = const_handler

    @abstractmethod
    def create_process_options(self, cmd: list):
        pass

class LocalRunHandler(BaseRunHandler):
    def __init__(self, config: dict, const_handler):
        super().__init__(config, const_handler)
    def create_process_options(self, cmd: list) -> ShellRequest:
        # コマンド配列内の各要素に対して変数展開
        return ShellRequest(cmd)

class DockerRunHandler(BaseRunHandler):
    def __init__(self, config: dict, const_handler):
        super().__init__(config, const_handler)

    def create_process_options(self, cmd: list) -> DockerRequest:
        # DockerRequest(EXEC)を返す
        return DockerRequest(
            op=DockerOpType.EXEC,
            name=self.const_handler.container_name,
            command=" ".join(cmd)
        )