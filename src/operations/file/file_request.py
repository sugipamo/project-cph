from enum import Enum, auto
from src.operations.operation_type import OperationType
from src.operations.file.file_driver import LocalFileDriver

class FileOpType(Enum):
    READ = auto()
    WRITE = auto()
    EXISTS = auto()
    MOVE = auto()
    COPY = auto()
    COPYTREE = auto()
    REMOVE = auto()
    RMTREE = auto()
    DOCKER_CP = auto()

class FileRequest:
    def __init__(self, op: FileOpType, path, content=None, driver=None, dst_path=None, container=None, to_container=True, docker_driver=None):
        self.op = op  # FileOpType
        self.path = path
        self.content = content
        self._executed = False
        self._result = None
        self._driver = driver or LocalFileDriver()
        self.dst_path = dst_path  # move/copy/copytree用
        self.container = container  # docker_cp用
        self.to_container = to_container  # docker_cp用
        self.docker_driver = docker_driver  # docker_cp用

    @property
    def operation_type(self):
        return OperationType.FILE

    def execute(self):
        if self._executed:
            raise RuntimeError("This FileRequest has already been executed.")
        from .file_result import FileResult
        import time
        start_time = time.time()
        try:
            self._driver.path = self._driver.base_dir / self.path
            if self.op == FileOpType.READ:
                with self._driver.open("r", encoding="utf-8") as f:
                    content = f.read()
                self._result = FileResult(success=True, content=content, path=self.path, op=self.op, request=self, start_time=start_time, end_time=time.time())
            elif self.op == FileOpType.WRITE:
                with self._driver.open("w", encoding="utf-8") as f:
                    f.write(self.content or "")
                self._result = FileResult(success=True, path=self.path, op=self.op, request=self, start_time=start_time, end_time=time.time())
            elif self.op == FileOpType.EXISTS:
                exists = self._driver.exists()
                self._result = FileResult(success=True, exists=exists, path=self.path, op=self.op, request=self, start_time=start_time, end_time=time.time())
            elif self.op == FileOpType.MOVE:
                self._driver.dst_path = self._driver.base_dir / self.dst_path
                self._driver.move()
                self._result = FileResult(success=True, path=self.path, op=self.op, request=self, start_time=start_time, end_time=time.time())
            elif self.op == FileOpType.COPY:
                self._driver.dst_path = self._driver.base_dir / self.dst_path
                self._driver.copy()
                self._result = FileResult(success=True, path=self.path, op=self.op, request=self, start_time=start_time, end_time=time.time())
            elif self.op == FileOpType.COPYTREE:
                self._driver.dst_path = self._driver.base_dir / self.dst_path
                self._driver.copytree()
                self._result = FileResult(success=True, path=self.path, op=self.op, request=self, start_time=start_time, end_time=time.time())
            elif self.op == FileOpType.REMOVE:
                self._driver.remove()
                self._result = FileResult(success=True, path=self.path, op=self.op, request=self, start_time=start_time, end_time=time.time())
            elif self.op == FileOpType.RMTREE:
                self._driver.rmtree()
                self._result = FileResult(success=True, path=self.path, op=self.op, request=self, start_time=start_time, end_time=time.time())
            elif self.op == FileOpType.DOCKER_CP:
                # path: src, dst_path: dst, container, to_container, docker_driver
                self._driver.docker_cp(self.path, self.dst_path, self.container, to_container=self.to_container, docker_driver=self.docker_driver)
                self._result = FileResult(success=True, path=self.path, op=self.op, request=self, start_time=start_time, end_time=time.time())
            else:
                self._result = FileResult(success=False, path=self.path, op=self.op, request=self, start_time=start_time, end_time=time.time(), error_message="Unknown operation")
        except Exception as e:
            self._result = FileResult(success=False, path=self.path, op=self.op, request=self, start_time=start_time, end_time=time.time(), error_message=str(e), exception=e)
        self._executed = True
        return self._result 