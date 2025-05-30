from src.operations.shell.shell_driver import ShellDriver

class DummyShellDriver(ShellDriver):
    """
    最小実装のスタブシェルドライバー
    - エラーを起こさない
    - 空の結果を返す
    - 内部状態や操作記録は持たない
    """
    
    def run(self, cmd, cwd=None, env=None, inputdata=None, timeout=None):
        """常に成功した空の結果を返す"""
        class DummyResult:
            def __init__(self):
                self.stdout = ""
                self.stderr = ""
                self.returncode = 0
        
        return DummyResult()