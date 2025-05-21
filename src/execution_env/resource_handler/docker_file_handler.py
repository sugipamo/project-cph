import os
from pathlib import Path
from src.operations.file.file_request import FileRequest, FileOpType
from src.operations.docker.docker_file_request import DockerFileRequest
from src.execution_env.resource_handler.base_file_handler import BaseFileHandler
from src.execution_env.resource_handler.path_environment_checker import PathEnvironmentChecker

class DockerFileHandler(BaseFileHandler):
    def __init__(self, config, const_handler):
        super().__init__(config, const_handler)
        self.path_env_checker = PathEnvironmentChecker(self.const_handler.workspace_path)

    def read(self, relative_path: str):
        return FileRequest(FileOpType.READ, relative_path)

    def write(self, relative_path: str, content: str):
        return FileRequest(FileOpType.WRITE, relative_path, content=content)

    def exists(self, relative_path: str):
        return FileRequest(FileOpType.EXISTS, relative_path)

    def copy(self, relative_path: str, target_path: str):
        src_path = relative_path
        if not os.path.isabs(src_path):
            ws = getattr(self.const_handler, 'workspace_path', None)
            if ws:
                src_path_full = os.path.join(ws, src_path)
            else:
                src_path_full = src_path
        else:
            src_path_full = src_path
        if os.path.isdir(src_path_full):
            return self.copytree(relative_path, target_path)
        src_in_ws = self.path_env_checker.is_in_container(relative_path)
        dst_in_ws = self.path_env_checker.is_in_container(target_path)
        container = self.const_handler.container_name
        if src_in_ws == dst_in_ws:
            return FileRequest(FileOpType.COPY, relative_path, dst_path=target_path)
        to_container = dst_in_ws and not src_in_ws
        req = DockerFileRequest(
            src_path=relative_path,
            dst_path=target_path,
            container=container,
            to_container=to_container
        )
        return req

    def move(self, src_path: str, dst_path: str):
        src_in_ws = self.path_env_checker.is_in_container(src_path)
        dst_in_ws = self.path_env_checker.is_in_container(dst_path)
        container = self.const_handler.container_name
        if src_in_ws == dst_in_ws:
            return FileRequest(FileOpType.MOVE, src_path, dst_path=dst_path)
        to_container = dst_in_ws and not src_in_ws
        req = DockerFileRequest(
            src_path=src_path,
            dst_path=dst_path,
            container=container,
            to_container=to_container
        )
        return req

    def remove(self, relative_path: str):
        in_ws = self.path_env_checker.is_in_container(relative_path)
        container = self.const_handler.container_name
        if in_ws:
            return FileRequest(FileOpType.REMOVE, relative_path)
        req = DockerFileRequest(
            src_path=relative_path,
            dst_path=None,
            container=container,
            to_container=False
        )
        return req

    def copytree(self, src_path: str, dst_path: str):
        src_in_ws = self.path_env_checker.is_in_container(src_path)
        dst_in_ws = self.path_env_checker.is_in_container(dst_path)
        container = self.const_handler.container_name
        if src_in_ws == dst_in_ws:
            return FileRequest(FileOpType.COPYTREE, src_path, dst_path=dst_path)
        to_container = dst_in_ws and not src_in_ws
        req = DockerFileRequest(
            src_path=src_path,
            dst_path=dst_path,
            container=container,
            to_container=to_container
        )
        return req

    def rmtree(self, dir_path: str):
        in_ws = self.path_env_checker.is_in_container(dir_path)
        container = self.const_handler.container_name
        if in_ws:
            return FileRequest(FileOpType.RMTREE, dir_path)
        req = DockerFileRequest(
            src_path=dir_path,
            dst_path=None,
            container=container,
            to_container=False
        )
        return req 