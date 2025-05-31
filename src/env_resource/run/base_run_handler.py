from abc import ABC, abstractmethod
from src.context.execution_context import ExecutionContext

class BaseRunHandler(ABC):
    def __init__(self, config: ExecutionContext, const_handler=None):
        self.config = config
        self.const_handler = const_handler

    @abstractmethod
    def create_process_options(self, cmd: list):
        pass 