from abc import ABC, abstractmethod
from src.context.execution_context import ExecutionContext

class BaseFileHandler(ABC):
    def __init__(self, config: ExecutionContext, const_handler):
        self.config = config
        self.const_handler = const_handler

    @abstractmethod
    def read(self, relative_path: str):
        pass

    @abstractmethod
    def write(self, relative_path: str, content: str):
        pass

    @abstractmethod
    def exists(self, relative_path: str):
        pass

    @abstractmethod
    def copy(self, relative_path: str, target_path: str):
        pass

    @abstractmethod
    def remove(self, relative_path: str):
        pass

    @abstractmethod
    def move(self, src_path: str, dst_path: str):
        pass

    @abstractmethod
    def copytree(self, src_path: str, dst_path: str):
        pass

    @abstractmethod
    def rmtree(self, dir_path: str):
        pass 