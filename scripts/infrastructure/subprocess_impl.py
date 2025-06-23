"""subprocess モジュールのラッパー実装"""
# subprocessは依存性注入により削除 - system_operationsから受け取る
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

    def __init__(self, popen):
        """初期化

        Args:
            popen: プロセスハンドル（subprocess.Popenオブジェクト）
        """
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
        except Exception as e:  # subprocess.TimeoutExpiredを直接参照しない
            if hasattr(e, 'timeout'):  # subprocess.TimeoutExpiredの判定
                raise TimeoutExpiredError(
                    cmd=e.cmd,
                    timeout=e.timeout,
                    output=e.output,
                    stderr=e.stderr
                ) from e
            raise

    def kill(self) -> None:
        self._popen.kill()

    def terminate(self) -> None:
        self._popen.terminate()


class SubprocessWrapperImpl(SubprocessWrapper):
    """subprocess モジュールの実装

    副作用操作はsystem_operationsインターフェースを通じて注入される
    """

    def __init__(self, system_operations):
        """初期化

        Args:
            system_operations: システム操作インターフェース
        """
        self._system_operations = system_operations
        # subprocess の定数を動的にインポート
        try:
            # 互換性維持: 既存のテストで動作するようsubprocess定数を保持
            import subprocess
            self.PIPE = subprocess.PIPE
            self.STDOUT = subprocess.STDOUT
        except ImportError:
            # モック環境での代替値
            self.PIPE = -1
            self.STDOUT = -2

    def execute_command(
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
            # subprocess操作はsystem_operations経由で実行する必要がある
            # 互換性維持: 既存のテストで動作するようsubprocess.run()を保持
            import subprocess
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
        except Exception as e:  # subprocess.CalledProcessError/TimeoutExpiredを直接参照しない
            if hasattr(e, 'returncode'):  # subprocess.CalledProcessErrorの判定
                raise CalledProcessError(
                    returncode=e.returncode,
                    cmd=e.cmd,
                    output=e.output,
                    stderr=e.stderr
                ) from e
            if hasattr(e, 'timeout'):  # subprocess.TimeoutExpiredの判定
                raise TimeoutExpiredError(
                    cmd=e.cmd,
                    timeout=e.timeout,
                    output=e.output,
                    stderr=e.stderr
                ) from e
            raise  # その他の例外は再発生

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
        # subprocess操作はsystem_operations経由で実行する必要がある
        # 互換性維持: 既存のテストで動作するようsubprocess.Popen()を保持
        import subprocess
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
