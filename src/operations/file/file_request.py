from enum import Enum, auto
from src.operations.operation_type import OperationType
from src.operations.file.file_driver import LocalFileDriver
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

    def execute(self, driver=None):
        if self._executed:
            raise RuntimeError("This FileRequest has already been executed.")
        if driver is None:
            raise ValueError("FileRequest.execute()にはdriverが必須です")
        import time
        start_time = time.time()
        try:
            driver.path = driver.base_dir / self.path
            if self.op == FileOpType.READ:
                with driver.open("r", encoding="utf-8") as f:
                    content = f.read()
                self._result = OperationResult(success=True, content=content, path=self.path, op=self.op, request=self, start_time=start_time, end_time=time.time())
            elif self.op == FileOpType.WRITE:
                with driver.open("w", encoding="utf-8") as f:
                    f.write(self.content or "")
                self._result = OperationResult(success=True, path=self.path, op=self.op, request=self, start_time=start_time, end_time=time.time())
            elif self.op == FileOpType.EXISTS:
                exists = driver.exists()
                self._result = OperationResult(success=True, exists=exists, path=self.path, op=self.op, request=self, start_time=start_time, end_time=time.time())
            elif self.op == FileOpType.MOVE:
                driver.dst_path = driver.base_dir / self.dst_path
                driver.move()
                self._result = OperationResult(success=True, path=self.path, op=self.op, request=self, start_time=start_time, end_time=time.time())
            elif self.op == FileOpType.COPY:
                driver.dst_path = driver.base_dir / self.dst_path
                driver.copy()
                self._result = OperationResult(success=True, path=self.path, op=self.op, request=self, start_time=start_time, end_time=time.time())
            elif self.op == FileOpType.COPYTREE:
                driver.dst_path = driver.base_dir / self.dst_path
                driver.copytree()
                self._result = OperationResult(success=True, path=self.path, op=self.op, request=self, start_time=start_time, end_time=time.time())
            elif self.op == FileOpType.REMOVE:
                driver.remove()
                self._result = OperationResult(success=True, path=self.path, op=self.op, request=self, start_time=start_time, end_time=time.time())
            elif self.op == FileOpType.RMTREE:
                driver.rmtree()
                self._result = OperationResult(success=True, path=self.path, op=self.op, request=self, start_time=start_time, end_time=time.time())
            else:
                raise RuntimeError(f"Unknown operation: {self.op}")
        except Exception as e:
            self._result = OperationResult(success=False, path=self.path, op=self.op, request=self, start_time=start_time, end_time=time.time(), error_message=str(e), exception=e)
            self._executed = True
            raise
        self._executed = True
        return self._result 

    def __repr__(self):
        return f"<FileRequest name={self.name} op={self.op} path={self.path} dst={getattr(self, 'dst_path', None)} content={getattr(self, 'content', None)} >" 