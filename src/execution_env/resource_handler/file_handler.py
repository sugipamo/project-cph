import os
from abc import ABC, abstractmethod
from src.operations.file.file_request import FileRequest, FileOpType

class BaseFileHandler(ABC):
    def __init__(self, config: dict, const_handler):
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
    

class DockerFileHandler(BaseFileHandler):
    def read(self, relative_path: str):
        path = self.const_handler.parse(relative_path)
        return FileRequest(FileOpType.READ, path)

    def write(self, relative_path: str, content: str):
        path = self.const_handler.parse(relative_path)
        return FileRequest(FileOpType.WRITE, path, content=content)

    def exists(self, relative_path: str):
        path = self.const_handler.parse(relative_path)
        return FileRequest(FileOpType.EXISTS, path)

    def copy(self, relative_path: str, target_path: str):
        path = self.const_handler.parse(relative_path)
        target_path = self.const_handler.parse(target_path)
        return FileRequest(FileOpType.COPY, path, target_path)

class LocalFileHandler(BaseFileHandler):
    def read(self, relative_path: str):
        path = self.const_handler.parse(relative_path)
        return FileRequest(FileOpType.READ, path)

    def write(self, relative_path: str, content: str):
        path = self.const_handler.parse(relative_path)
        return FileRequest(FileOpType.WRITE, path, content=content)

    def exists(self, relative_path: str):
        path = self.const_handler.parse(relative_path)
        return FileRequest(FileOpType.EXISTS, path)

    def copy(self, relative_path: str, target_path: str):
        path = self.const_handler.parse(relative_path)
        target_path = self.const_handler.parse(target_path)
        return FileRequest(FileOpType.COPY, path, target_path)
        