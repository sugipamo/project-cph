"""subprocess モジュールの抽象化

subprocess モジュールの副作用を依存性注入可能な形で抽象化
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Union


@dataclass
class ProcessResult:
    """プロセス実行結果"""
    returncode: int
    stdout: Optional[str]
    stderr: Optional[str]
    args: Union[str, List[str]]


class SubprocessWrapper(ABC):
    """subprocess操作のインターフェース"""

    @abstractmethod
    def run(
        self,
        args: Union[str, List[str]],
        capture_output: bool,
        text: bool,
        cwd: Optional[str],
        timeout: Optional[float],
        env: Optional[Dict[str, str]],
        check: bool,
        shell: bool
    ) -> ProcessResult:
        """コマンドを実行して完了を待つ

        Args:
            args: 実行するコマンド
            capture_output: 出力をキャプチャするか
            text: テキストモードで実行するか
            cwd: 作業ディレクトリ
            timeout: タイムアウト（秒）
            env: 環境変数
            check: 非ゼロ終了コードで例外を発生させるか
            shell: シェル経由で実行するか

        Returns:
            ProcessResult: 実行結果
        """
        pass

    @abstractmethod
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
    ) -> 'ProcessHandle':
        """新しいプロセスを作成

        Args:
            args: 実行するコマンド
            stdout: 標準出力の扱い
            stderr: 標準エラー出力の扱い
            text: テキストモードで実行するか
            cwd: 作業ディレクトリ
            env: 環境変数
            bufsize: バッファサイズ
            universal_newlines: 改行文字を統一するか

        Returns:
            ProcessHandle: プロセスハンドル
        """
        pass


class ProcessHandle(ABC):
    """実行中のプロセスのハンドル"""

    @property
    @abstractmethod
    def stdout(self) -> Any:
        """標準出力ストリーム"""
        pass

    @property
    @abstractmethod
    def stderr(self) -> Any:
        """標準エラー出力ストリーム"""
        pass

    @property
    @abstractmethod
    def returncode(self) -> Optional[int]:
        """プロセスの終了コード"""
        pass

    @abstractmethod
    def wait(self, timeout: Optional[float]) -> int:
        """プロセスの完了を待つ

        Args:
            timeout: タイムアウト（秒）

        Returns:
            int: 終了コード
        """
        pass

    @abstractmethod
    def kill(self) -> None:
        """プロセスを強制終了"""
        pass

    @abstractmethod
    def terminate(self) -> None:
        """プロセスを終了"""
        pass


class CalledProcessError(Exception):
    """プロセスが非ゼロで終了した場合の例外"""
    def __init__(self, returncode: int, cmd: Union[str, List[str]], output: Optional[str], stderr: Optional[str]):
        self.returncode = returncode
        self.cmd = cmd
        self.output = output
        self.stderr = stderr
        super().__init__(f"Command '{cmd}' returned non-zero exit status {returncode}.")


class TimeoutExpiredError(Exception):
    """プロセスがタイムアウトした場合の例外"""
    def __init__(self, cmd: Union[str, List[str]], timeout: float, output: Optional[str], stderr: Optional[str]):
        self.cmd = cmd
        self.timeout = timeout
        self.output = output
        self.stderr = stderr
        super().__init__(f"Command '{cmd}' timed out after {timeout} seconds")
