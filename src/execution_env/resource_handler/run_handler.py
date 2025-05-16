from abc import ABC, abstractmethod
from typing import List
from src.shell_process import ShellProcessOptions


class BaseRunHandler(ABC):
    def __init__(self, config: dict, const_handler):
        self.config = config
        self.const_handler = const_handler

    @abstractmethod
    def create_process_options(self, cmd: List[str]) -> ShellProcessOptions:
        pass

class LocalRunHandler(BaseRunHandler):
    def create_process_options(self, cmd: List[str]) -> ShellProcessOptions:
        # コマンド配列内の各要素に対して変数展開
        parsed_cmd = [self.const_handler.parse(c) for c in cmd]
        return ShellProcessOptions(parsed_cmd)

class DockerRunHandler(BaseRunHandler):
    def create_process_options(self, cmd: List[str]) -> ShellProcessOptions:
        # コマンド配列内の各要素に対して変数展開（Docker用パスで）
        parsed_cmd = [self.const_handler.parse(c) for c in cmd]
        return ShellProcessOptions(parsed_cmd)