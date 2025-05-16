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
        return FileRequest(FileOpType.READ, relative_path)

    def write(self, relative_path: str, content: str):
        return FileRequest(FileOpType.WRITE, relative_path, content=content)

    def exists(self, relative_path: str):
        return FileRequest(FileOpType.EXISTS, relative_path)

    def copy(self, relative_path: str, target_path: str):
        return FileRequest(FileOpType.COPY, relative_path, target_path)

class LocalFileHandler(BaseFileHandler):
    def read(self, relative_path: str):
        return FileRequest(FileOpType.READ, relative_path)

    def write(self, relative_path: str, content: str):
        return FileRequest(FileOpType.WRITE, relative_path, content=content)

    def exists(self, relative_path: str):
        return FileRequest(FileOpType.EXISTS, relative_path)

    def copy(self, relative_path: str, target_path: str):
        return FileRequest(FileOpType.COPY, relative_path, target_path)
        