class ShellRequest:
    def __init__(self, cmd, cwd=None, env=None):
        self.cmd = cmd
        self.cwd = cwd
        self.env = env
        self._executed = False
        self._result = None

    def execute(self):
        if self._executed:
            raise RuntimeError("This ShellRequest has already been executed.")
        # 実際のコマンド実行はshell_process等を利用する想定
        # ここではダミーのShellResultを返す
        from .shell_result import ShellResult
        # TODO: 実際のコマンド実行処理に置き換え
        self._result = ShellResult(stdout="", stderr="", returncode=0)
        self._executed = True
        return self._result 