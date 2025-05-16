from enum import Enum, auto
from src.operations.operation_type import OperationType

class FileOpType(Enum):
    READ = auto()
    WRITE = auto()
    EXISTS = auto()

class FileRequest:
    def __init__(self, op: FileOpType, path, content=None):
        self.op = op  # FileOpType
        self.path = path
        self.content = content
        self._executed = False
        self._result = None

    @property
    def operation_type(self):
        return OperationType.FILE

    def execute(self):
        if self._executed:
            raise RuntimeError("This FileRequest has already been executed.")
        from .file_result import FileResult
        # TODO: 実際のファイル操作処理に置き換え
        if self.op == FileOpType.READ:
            # 仮実装: 空文字列を返す
            self._result = FileResult(success=True, content="")
        elif self.op == FileOpType.WRITE:
            self._result = FileResult(success=True)
        elif self.op == FileOpType.EXISTS:
            self._result = FileResult(success=True, exists=True)
        else:
            self._result = FileResult(success=False)
        self._executed = True
        return self._result 