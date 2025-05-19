import os
from abc import ABC, abstractmethod
from typing import List
from src.operations.file.file_request import FileRequest, FileOpType
from pathlib import Path
from src.operations.file.file_driver import LocalFileDriver
from src.operations.docker.docker_file_request import DockerFileRequest
from src.execution_context.env_context import EnvContext

class BaseFileHandler(ABC):
    def __init__(self, config: EnvContext, const_handler):
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

class DockerFileHandler(BaseFileHandler):
    def __init__(self, config: EnvContext, const_handler):
        super().__init__(config, const_handler)

    def _is_in_container(self, path: str) -> bool:
        ws = Path(self.const_handler.workspace_path).resolve()
        p = Path(path).resolve()
        if p.is_absolute():
            target = p.resolve()
        else:
            target = (ws / p).resolve()
        try:
            target.relative_to(ws)
            return True
        except ValueError:
            return False

    def read(self, relative_path: str):
        return FileRequest(FileOpType.READ, relative_path)

    def write(self, relative_path: str, content: str):
        return FileRequest(FileOpType.WRITE, relative_path, content=content)

    def exists(self, relative_path: str):
        return FileRequest(FileOpType.EXISTS, relative_path)

    def copy(self, relative_path: str, target_path: str):
        # ディレクトリかどうかを判定し、適切なFileRequestを返す
        src_path = relative_path
        # src_pathが絶対パスでなければworkspace基準で解決
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
        src_in_ws = self._is_in_container(relative_path)
        dst_in_ws = self._is_in_container(target_path)
        container = self.const_handler.container_name
        if src_in_ws == dst_in_ws:
            return FileRequest(FileOpType.COPY, relative_path, dst_path=target_path)
        # どちらかが外の場合
        to_container = dst_in_ws and not src_in_ws
        req = DockerFileRequest(
            src_path=relative_path,
            dst_path=target_path,
            container=container,
            to_container=to_container
        )
        return req

    def move(self, src_path: str, dst_path: str):
        src_in_ws = self._is_in_container(src_path)
        dst_in_ws = self._is_in_container(dst_path)
        container = self.const_handler.container_name
        if src_in_ws == dst_in_ws:
            return FileRequest(FileOpType.MOVE, src_path, dst_path=dst_path)
        # どちらかが外の場合はcopy+remove相当（ここではcopyのみ返す。上位層で合成も可）
        to_container = dst_in_ws and not src_in_ws
        req = DockerFileRequest(
            src_path=src_path,
            dst_path=dst_path,
            container=container,
            to_container=to_container
        )
        return req

    def remove(self, relative_path: str):
        in_ws = self._is_in_container(relative_path)
        container = self.const_handler.container_name
        if in_ws:
            return FileRequest(FileOpType.REMOVE, relative_path)
        # ホスト側のファイル削除（DOCKER_RM等があればそちらを使う。なければ例外や警告も検討）
        # ここではDockerFileRequestで表現できる範囲で返す
        req = DockerFileRequest(
            src_path=relative_path,
            dst_path=None,
            container=container,
            to_container=False
        )
        return req

    def copytree(self, src_path: str, dst_path: str):
        src_in_ws = self._is_in_container(src_path)
        dst_in_ws = self._is_in_container(dst_path)
        container = self.const_handler.container_name
        if src_in_ws == dst_in_ws:
            return FileRequest(FileOpType.COPYTREE, src_path, dst_path=dst_path)
        # どちらかが外の場合
        to_container = dst_in_ws and not src_in_ws
        req = DockerFileRequest(
            src_path=src_path,
            dst_path=dst_path,
            container=container,
            to_container=to_container
        )
        return req

    def rmtree(self, dir_path: str):
        in_ws = self._is_in_container(dir_path)
        container = self.const_handler.container_name
        if in_ws:
            return FileRequest(FileOpType.RMTREE, dir_path)
        # ホスト側のディレクトリ削除（DOCKER_RM等があればそちらを使う。なければ例外や警告も検討）
        req = DockerFileRequest(
            src_path=dir_path,
            dst_path=None,
            container=container,
            to_container=False
        )
        return req

class LocalFileHandler(BaseFileHandler):
    def __init__(self, config: EnvContext, const_handler):
        super().__init__(config, const_handler)

    def read(self, relative_path: str):
        return FileRequest(FileOpType.READ, relative_path)

    def write(self, relative_path: str, content: str):
        return FileRequest(FileOpType.WRITE, relative_path, content=content)

    def exists(self, relative_path: str):
        return FileRequest(FileOpType.EXISTS, relative_path)

    def copy(self, relative_path: str, target_path: str):
        # ディレクトリかどうかを判定し、適切なFileRequestを返す
        src_path = relative_path
        # src_pathが絶対パスでなければworkspace基準で解決
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
        return FileRequest(FileOpType.COPY, relative_path, dst_path=target_path)

    def remove(self, relative_path: str):
        return FileRequest(FileOpType.REMOVE, relative_path)

    def move(self, src_path: str, dst_path: str):
        return FileRequest(FileOpType.MOVE, src_path, dst_path=dst_path)

    def copytree(self, src_path: str, dst_path: str):
        return FileRequest(FileOpType.COPYTREE, src_path, dst_path=dst_path)

    def rmtree(self, dir_path: str):
        return FileRequest(FileOpType.RMTREE, dir_path)
        