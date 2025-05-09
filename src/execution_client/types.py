from typing import Optional, Any

class ExecutionResult:
    def __init__(self, returncode: int, stdout: Optional[str] = None, stderr: Optional[str] = None, extra: Optional[Any] = None):
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr
        self.extra = extra 