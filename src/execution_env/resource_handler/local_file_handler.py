import os
from src.operations.file.file_request import FileRequest, FileOpType
from src.execution_env.resource_handler.base_file_handler import BaseFileHandler

class LocalFileHandler(BaseFileHandler):
    def __init__(self, config, const_handler):
        super().__init__(config, const_handler)

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
        return FileRequest(FileOpType.COPY, relative_path, dst_path=target_path)

    def remove(self, relative_path: str):
        return FileRequest(FileOpType.REMOVE, relative_path)

    def move(self, src_path: str, dst_path: str):
        return FileRequest(FileOpType.MOVE, src_path, dst_path=dst_path)

    def copytree(self, src_path: str, dst_path: str):
        return FileRequest(FileOpType.COPYTREE, src_path, dst_path=dst_path)

    def rmtree(self, dir_path: str):
        return FileRequest(FileOpType.RMTREE, dir_path) 