import subprocess
from .shell_driver import ShellDriver

class LocalShellDriver(ShellDriver):
    def run(self, cmd, cwd=None, env=None, inputdata=None, timeout=None):
        return subprocess.run(
            cmd,
            input=inputdata,
            cwd=cwd,
            env=env,
            text=True,
            capture_output=True,
            timeout=timeout
        ) 