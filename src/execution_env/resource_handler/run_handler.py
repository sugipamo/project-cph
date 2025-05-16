from abc import ABC, abstractmethod
from typing import List
from src.shell_process import ShellProcessOptions


class BaseRunHandler(ABC):
    def __init__(self, config: dict):
        self.config = config

    @abstractmethod
    def create_process_options(self, cmd: List[str]) -> ShellProcessOptions:
        pass

class LocalRunHandler(BaseRunHandler):
    def create_process_options(self, cmd: List[str]) -> ShellProcessOptions:
        # ここでローカル用のShellProcessOptionsを生成
        # 必要に応じてself.configやconst_handlerのparseを使う
        return ShellProcessOptions(cmd)

class DockerRunHandler(BaseRunHandler):
    def create_process_options(self, cmd: List[str]) -> ShellProcessOptions:
        # ここでDocker用のShellProcessOptionsを生成
        # 必要に応じてself.configやconst_handlerのparseを使う
        return ShellProcessOptions(cmd)