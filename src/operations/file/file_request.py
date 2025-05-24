from enum import Enum, auto
from src.operations.constants.operation_type import OperationType
from src.operations.file.local_file_driver import LocalFileDriver
from src.operations.result import OperationResult
from src.operations.base_request import BaseRequest
import inspect
import os

class FileOpType(Enum):
    READ = auto()
    WRITE = auto()
    EXISTS = auto()
    MOVE = auto()
    COPY = auto()
    COPYTREE = auto()
    REMOVE = auto()
    RMTREE = auto()
    MKDIR = auto()
    TOUCH = auto()

class FileRequest(BaseRequest):
    def __init__(self, op: FileOpType, path, content=None, dst_path=None, debug_tag=None, name=None):
        super().__init__(name=name, debug_tag=debug_tag)
        self.op = op  # FileOpType
        self.path = path
        self.content = content
        self.dst_path = dst_path  # move/copy/copytree用
        self._executed = False
        self._result = None

    def set_name(self, name: str):
        self.name = name
        return self

    @property
    def operation_type(self):
        return OperationType.FILE

    def execute(self, driver):
        return super().execute(driver)

    def _execute_core(self, driver):
        import time
        start_time = time.time()
        try:
            driver.path = driver.base_dir / self.path
            if self.op == FileOpType.READ:
                with driver.open("r", encoding="utf-8") as f:
                    content = f.read()
                return OperationResult(success=True, content=content, path=self.path, op=self.op, request=self, start_time=start_time, end_time=time.time())
            elif self.op == FileOpType.WRITE:
                with driver.open("w", encoding="utf-8") as f:
                    f.write(self.content or "")
                return OperationResult(success=True, path=self.path, op=self.op, request=self, start_time=start_time, end_time=time.time())
            elif self.op == FileOpType.EXISTS:
                exists = driver.exists()
                return OperationResult(success=True, exists=exists, path=self.path, op=self.op, request=self, start_time=start_time, end_time=time.time())
            elif self.op == FileOpType.MOVE:
                driver.dst_path = driver.base_dir / self.dst_path
                driver.move()
                return OperationResult(success=True, path=self.path, op=self.op, request=self, start_time=start_time, end_time=time.time())
            elif self.op == FileOpType.COPY:
                driver.dst_path = driver.base_dir / self.dst_path
                driver.copy()
                return OperationResult(success=True, path=self.path, op=self.op, request=self, start_time=start_time, end_time=time.time())
            elif self.op == FileOpType.COPYTREE:
                driver.dst_path = driver.base_dir / self.dst_path
                driver.copytree()
                return OperationResult(success=True, path=self.path, op=self.op, request=self, start_time=start_time, end_time=time.time())
            elif self.op == FileOpType.REMOVE:
                driver.remove()
                return OperationResult(success=True, path=self.path, op=self.op, request=self, start_time=start_time, end_time=time.time())
            elif self.op == FileOpType.RMTREE:
                driver.rmtree()
                return OperationResult(success=True, path=self.path, op=self.op, request=self, start_time=start_time, end_time=time.time())
            elif self.op == FileOpType.MKDIR:
                driver.mkdir()
                return OperationResult(success=True, path=self.path, op=self.op, request=self, start_time=start_time, end_time=time.time())
            elif self.op == FileOpType.TOUCH:
                driver.touch()
                return OperationResult(success=True, path=self.path, op=self.op, request=self, start_time=start_time, end_time=time.time())
            else:
                raise RuntimeError(f"Unknown operation: {self.op}")
        except Exception as e:
            raise RuntimeError(f"FileRequest failed: {str(e)}")

    def __repr__(self):
        return f"<FileRequest name={self.name} op={self.op} path={self.path} dst={getattr(self, 'dst_path', None)} content={getattr(self, 'content', None)} >" 