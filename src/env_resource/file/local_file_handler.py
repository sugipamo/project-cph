import os
from src.operations.file.file_request import FileRequest, FileOpType
from src.env_resource.file.base_file_handler import BaseFileHandler
from src.context.execution_context import ExecutionContext
from src.env_resource.utils.path_utils import get_workspace_path

class LocalFileHandler(BaseFileHandler):
    def __init__(self, config, const_handler=None):
        super().__init__(config, const_handler)
        if config and hasattr(config, 'resolver') and hasattr(config, 'language'):
            self.workspace_path = get_workspace_path(config.resolver, config.language)
        else:
            self.workspace_path = None

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
        return FileRequest(FileOpType.COPY, relative_path, dst_path=target_path)

    def remove(self, relative_path: str):
        return FileRequest(FileOpType.REMOVE, relative_path)

    def move(self, src_path: str, dst_path: str):
        return FileRequest(FileOpType.MOVE, src_path, dst_path=dst_path)

    def copytree(self, src_path: str, dst_path: str):
        return FileRequest(FileOpType.COPYTREE, src_path, dst_path=dst_path)

    def rmtree(self, dir_path: str):
        return FileRequest(FileOpType.RMTREE, dir_path) 