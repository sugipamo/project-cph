import os
from abc import ABC, abstractmethod

class BaseFileHandler(ABC):
    def __init__(self, config: dict, const_handler):
        self.config = config
        self.const_handler = const_handler

    @abstractmethod
    def read(self, relative_path: str) -> str:
        pass

    @abstractmethod
    def write(self, relative_path: str, content: str):
        pass

    @abstractmethod
    def exists(self, relative_path: str) -> bool:
        pass

class DockerFileHandler(BaseFileHandler):
    def read(self, relative_path: str) -> str:
        raise NotImplementedError("DockerFileHandler.readは未実装です")

    def write(self, relative_path: str, content: str):
        raise NotImplementedError("DockerFileHandler.writeは未実装です")

    def exists(self, relative_path: str) -> bool:
        raise NotImplementedError("DockerFileHandler.existsは未実装です")

class LocalFileHandler(BaseFileHandler):
    def read(self, relative_path: str) -> str:
        path = self.const_handler.parse(relative_path)
        with open(path, 'r', encoding='utf-8') as f:
            return f.read()

    def write(self, relative_path: str, content: str):
        path = self.const_handler.parse(relative_path)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)

    def exists(self, relative_path: str) -> bool:
        path = self.const_handler.parse(relative_path)
        return os.path.exists(path)