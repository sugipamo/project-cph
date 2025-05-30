from .shell_driver import ShellDriver
from .shell_util import ShellUtil

class LocalShellDriver(ShellDriver):
    def run(self, cmd, cwd=None, env=None, inputdata=None, timeout=None):
        return ShellUtil.run_subprocess(
            cmd=cmd,
            cwd=cwd,
            env=env,
            inputdata=inputdata,
            timeout=timeout
        ) 