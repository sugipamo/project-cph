"""subprocess モジュールのラッパー実装"""
import subprocess
from typing import Any, Dict, List, Optional, Union

from .subprocess_wrapper import (
    CalledProcessError,
    ProcessHandle,
    ProcessResult,
    SubprocessWrapper,
    TimeoutExpiredError,
)


class SubprocessProcessHandle(ProcessHandle):
    """subprocess.Popen のラッパー"""

    def __init__(self, popen: subprocess.Popen):
        self._popen = popen

    @property
    def stdout(self) -> Any:
        return self._popen.stdout

    @property
    def stderr(self) -> Any:
        return self._popen.stderr

    @property
    def returncode(self) -> Optional[int]:
        return self._popen.returncode

    def wait(self, timeout: Optional[float]) -> int:
        try:
            return self._popen.wait(timeout=timeout)
        except subprocess.TimeoutExpired as e:
            raise TimeoutExpiredError(
                cmd=e.cmd,
                timeout=e.timeout,
                output=e.output,
                stderr=e.stderr
            ) from e

    def kill(self) -> None:
        self._popen.kill()

    def terminate(self) -> None:
        self._popen.terminate()


class SubprocessWrapperImpl(SubprocessWrapper):
    """subprocess モジュールの実装"""

    # subprocess の定数を公開
    PIPE = subprocess.PIPE
    STDOUT = subprocess.STDOUT

    def run(
        self,
        args: Union[str, List[str]],
        capture_output: bool,
        text: bool,
        cwd: Optional[str],
        timeout: Optional[float],
        env: Optional[Dict[str, str]],
        check: bool,
        shell: bool = False
    ) -> ProcessResult:
        try:
            result = subprocess.run(
                args,
                capture_output=capture_output,
                text=text,
                cwd=cwd,
                timeout=timeout,
                env=env,
                check=check,
                shell=shell
            )
            return ProcessResult(
                returncode=result.returncode,
                stdout=result.stdout,
                stderr=result.stderr,
                args=result.args
            )
        except subprocess.CalledProcessError as e:
            raise CalledProcessError(
                returncode=e.returncode,
                cmd=e.cmd,
                output=e.output,
                stderr=e.stderr
            ) from e
        except subprocess.TimeoutExpired as e:
            raise TimeoutExpiredError(
                cmd=e.cmd,
                timeout=e.timeout,
                output=e.output,
                stderr=e.stderr
            ) from e

    def popen(
        self,
        args: Union[str, List[str]],
        stdout: Any,
        stderr: Any,
        text: bool,
        cwd: Optional[str],
        env: Optional[Dict[str, str]],
        bufsize: int,
        universal_newlines: bool
    ) -> ProcessHandle:
        popen = subprocess.Popen(
            args,
            stdout=stdout,
            stderr=stderr,
            text=text,
            cwd=cwd,
            env=env,
            bufsize=bufsize,
            universal_newlines=universal_newlines
        )
        return SubprocessProcessHandle(popen)
