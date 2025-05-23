from src.operations.shell.shell_driver import ShellDriver

class MockShellDriver(ShellDriver):
    def __init__(self):
        self.calls = []
    def run(self, cmd, cwd=None, env=None, inputdata=None, timeout=None):
        self.calls.append({
            'cmd': cmd,
            'cwd': cwd,
            'env': env,
            'inputdata': inputdata,
            'timeout': timeout
        })
        class Result:
            def __init__(self):
                self.stdout = 'mock_stdout'
                self.stderr = ''
                self.returncode = 0
        return Result() 