class FileRequest:
    def __init__(self, op, path, content=None):
        self.op = op  # 'read', 'write', 'exists' など
        self.path = path
        self.content = content
        self._executed = False
        self._result = None

    def execute(self):
        if self._executed:
            raise RuntimeError("This FileRequest has already been executed.")
        from .file_result import FileResult
        # TODO: 実際のファイル操作処理に置き換え
        if self.op == 'read':
            # 仮実装: 空文字列を返す
            self._result = FileResult(success=True, content="")
        elif self.op == 'write':
            self._result = FileResult(success=True)
        elif self.op == 'exists':
            self._result = FileResult(success=True, exists=True)
        else:
            self._result = FileResult(success=False)
        self._executed = True
        return self._result 