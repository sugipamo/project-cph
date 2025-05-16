from abc import ABC, abstractmethod
from typing import List
from src.operations.shell.shell_request import ShellRequest
from src.operations.docker.docker_request import DockerRequest, DockerOpType


class BaseRunHandler(ABC):
    def __init__(self, config: dict, const_handler):
        self.config = config
        self.const_handler = const_handler

    @abstractmethod
    def create_process_options(self, cmd: List[str]):
        pass

class LocalRunHandler(BaseRunHandler):
    def create_process_options(self, cmd: List[str]) -> ShellRequest:
        # コマンド配列内の各要素に対して変数展開
        return ShellRequest(cmd)

class DockerRunHandler(BaseRunHandler):
    def __init__(self, config: dict, const_handler, container_name: str):
        super().__init__(config, const_handler)
        self.container_name = container_name

    def create_process_options(self, cmd: List[str]) -> DockerRequest:
        # DockerRequest(EXEC)を返す
        return DockerRequest(
            op=DockerOpType.EXEC,
            name=self.container_name,
            command=" ".join(cmd)
        )