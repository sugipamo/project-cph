import os
from pathlib import Path
from src.operations.file.file_request import FileRequest, FileOpType
from src.operations.docker.docker_file_request import DockerFileRequest
from src.env.resource.file.base_file_handler import BaseFileHandler
from src.env.resource.utils.path_environment_checker import PathEnvironmentChecker
from src.context.execution_context import ExecutionContext
from src.env.resource.utils.path_utils import get_workspace_path
from src.env.resource.utils.docker_naming import get_container_name

class DockerFileHandler(BaseFileHandler):
    def __init__(self, config: ExecutionContext, const_handler=None):
        super().__init__(config, const_handler)
        if config and hasattr(config, 'resolver') and hasattr(config, 'language'):
            self.workspace_path = get_workspace_path(config.resolver, config.language)
            self.path_env_checker = PathEnvironmentChecker(self.workspace_path)
        else:
            self.workspace_path = None
            self.path_env_checker = None
    
    def get_container_name(self):
        if self.config and hasattr(self.config, 'language'):
            dockerfile_text = getattr(self.config, 'dockerfile', None)
            return get_container_name(self.config.language, dockerfile_text)
        return "dummy_container"  # Default for tests

    def read(self, relative_path: str):
        return FileRequest(FileOpType.READ, relative_path)

    def write(self, relative_path: str, content: str):
        return FileRequest(FileOpType.WRITE, relative_path, content=content)

    def exists(self, relative_path: str):
        return FileRequest(FileOpType.EXISTS, relative_path)

    def copy(self, relative_path: str, target_path: str):
        src_path = relative_path
        if not os.path.isabs(src_path) and self.workspace_path:
            ws = self.workspace_path
            src_path_full = os.path.join(str(ws), src_path)
        else:
            src_path_full = src_path
        if os.path.isdir(src_path_full):
            return self.copytree(relative_path, target_path)
        if self.path_env_checker:
            src_in_ws = self.path_env_checker.is_in_container(relative_path)
            dst_in_ws = self.path_env_checker.is_in_container(target_path)
        else:
            src_in_ws = dst_in_ws = False
        container = self.get_container_name()
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
        container = self.get_container_name()
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
        container = self.get_container_name()
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
        container = self.get_container_name()
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
        container = self.get_container_name()
        if in_ws:
            return FileRequest(FileOpType.RMTREE, dir_path)
        req = DockerFileRequest(
            src_path=dir_path,
            dst_path=None,
            container=container,
            to_container=False
        )
        return req 