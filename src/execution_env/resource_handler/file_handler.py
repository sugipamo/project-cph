import os
from abc import ABC, abstractmethod
from src.operations.file.file_request import FileRequest, FileOpType
from pathlib import Path

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
    def copy(self, relative_path: str, target_path: str, container: str, to_container: bool = None, docker_driver=None):
        pass
    

class DockerFileHandler(BaseFileHandler):
    def __init__(self, config: dict, const_handler):
        super().__init__(config, const_handler)

    def read(self, relative_path: str):
        return FileRequest(FileOpType.READ, relative_path)

    def write(self, relative_path: str, content: str):
        return FileRequest(FileOpType.WRITE, relative_path, content=content)

    def exists(self, relative_path: str):
        return FileRequest(FileOpType.EXISTS, relative_path)

    def copy(self, relative_path: str, target_path: str, container: str):
        ws = Path(self.const_handler.workspace)
        src = Path(relative_path)
        dst = Path(target_path)
        src_in_ws = str((ws / src).resolve()).startswith(str(ws.resolve()))
        dst_in_ws = str((ws / dst).resolve()).startswith(str(ws.resolve()))
        if src_in_ws and dst_in_ws:
            return FileRequest(FileOpType.COPY, relative_path, dst_path=target_path)
        # どちらかが外の場合
        to_container = src_in_ws and not dst_in_ws
        
        return FileRequest(FileOpType.DOCKER_CP, relative_path, dst_path=target_path, container=container, to_container=to_container, docker_driver=LocalDockerDriver())

class LocalFileHandler(BaseFileHandler):
    def read(self, relative_path: str):
        return FileRequest(FileOpType.READ, relative_path)

    def write(self, relative_path: str, content: str):
        return FileRequest(FileOpType.WRITE, relative_path, content=content)

    def exists(self, relative_path: str):
        return FileRequest(FileOpType.EXISTS, relative_path)

    def copy(self, relative_path: str, target_path: str):
        return FileRequest(FileOpType.COPY, relative_path, target_path)
        