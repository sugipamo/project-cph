from .shell_driver import ShellDriver
from .shell_utils import ShellUtils

class LocalShellDriver(ShellDriver):
    def run(self, cmd, cwd=None, env=None, inputdata=None, timeout=None):
        return ShellUtils.run_subprocess(
            cmd=cmd,
            cwd=cwd,
            env=env,
            inputdata=inputdata,
            timeout=timeout
        ) 