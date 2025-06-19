"""外部コマンド実行の抽象化と実装

Scripts配下で2番目に重要な副作用であるsubprocess.runを
依存性注入可能な形で抽象化
"""
import subprocess
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Union


@dataclass
class CommandResult:
    """コマンド実行結果"""
    returncode: int
    stdout: str
    stderr: str
    success: bool

    @classmethod
    def from_subprocess_result(cls, result: subprocess.CompletedProcess) -> 'CommandResult':
        """subprocess.CompletedProcessから変換"""
        return cls(
            returncode=result.returncode,
            stdout=result.stdout or "",
            stderr=result.stderr or "",
            success=result.returncode == 0
        )


class CommandExecutor(ABC):
    """コマンド実行インターフェース"""

    @abstractmethod
    def run(
        self,
        cmd: Union[List[str], str],
        capture_output: bool = True,
        text: bool = True,
        cwd: Optional[str] = None,
        timeout: Optional[float] = None,
        env: Optional[Dict[str, str]] = None,
        check: bool = False
    ) -> CommandResult:
        """コマンドを実行する

        Args:
            cmd: 実行するコマンド（リストまたは文字列）
            capture_output: 出力をキャプチャするか
            text: テキストモードで実行するか
            cwd: 作業ディレクトリ
            timeout: タイムアウト（秒）
            env: 環境変数
            check: 非ゼロ終了コードで例外を発生させるか

        Returns:
            CommandResult: 実行結果
        """
        pass

    @abstractmethod
    def check_availability(self, command: str) -> bool:
        """コマンドが利用可能かチェック

        Args:
            command: チェックするコマンド名

        Returns:
            bool: コマンドが利用可能か
        """
        pass


class SubprocessCommandExecutor(CommandExecutor):
    """subprocess.runを使用した実装"""

    def run(
        self,
        cmd: Union[List[str], str],
        capture_output: bool = True,
        text: bool = True,
        cwd: Optional[str] = None,
        timeout: Optional[float] = None,
        env: Optional[Dict[str, str]] = None,
        check: bool = False
    ) -> CommandResult:
        """subprocess.runを使用してコマンドを実行"""
        try:
            result = subprocess.run(
                cmd,
                capture_output=capture_output,
                text=text,
                cwd=cwd,
                timeout=timeout,
                env=env,
                check=check
            )
            return CommandResult.from_subprocess_result(result)
        except subprocess.CalledProcessError as e:
            return CommandResult(
                returncode=e.returncode,
                stdout=e.stdout or "",
                stderr=e.stderr or "",
                success=False
            )
        except subprocess.TimeoutExpired as e:
            return CommandResult(
                returncode=-1,
                stdout=e.stdout or "",
                stderr=f"Timeout after {timeout} seconds",
                success=False
            )
        except FileNotFoundError as e:
            return CommandResult(
                returncode=-1,
                stdout="",
                stderr=f"Command not found: {e}",
                success=False
            )

    def check_availability(self, command: str) -> bool:
        """コマンドが利用可能かチェック"""
        try:
            result = subprocess.run(
                [command, "--version"],
                capture_output=True,
                text=True,
                timeout=10
            )
            return result.returncode == 0
        except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
            try:
                # --versionが使えない場合は-hを試す
                result = subprocess.run(
                    [command, "-h"],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                return result.returncode == 0
            except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
                return False


class MockCommandExecutor(CommandExecutor):
    """テスト用のモック実装"""

    def __init__(self):
        self.executed_commands: List[Dict[str, Any]] = []
        self.mock_results: Dict[str, CommandResult] = {}
        self.available_commands: set = set()

    def run(
        self,
        cmd: Union[List[str], str],
        capture_output: bool = True,
        text: bool = True,
        cwd: Optional[str] = None,
        timeout: Optional[float] = None,
        env: Optional[Dict[str, str]] = None,
        check: bool = False
    ) -> CommandResult:
        """モックコマンド実行"""
        # 実行されたコマンドを記録
        self.executed_commands.append({
            'cmd': cmd,
            'capture_output': capture_output,
            'text': text,
            'cwd': cwd,
            'timeout': timeout,
            'env': env,
            'check': check
        })

        # コマンドをキー化
        cmd_key = ' '.join(cmd) if isinstance(cmd, list) else cmd

        # モック結果があればそれを返す
        if cmd_key in self.mock_results:
            return self.mock_results[cmd_key]

        # デフォルトは成功
        return CommandResult(
            returncode=0,
            stdout="Mock output",
            stderr="",
            success=True
        )

    def check_availability(self, command: str) -> bool:
        """モックコマンド可用性チェック"""
        return command in self.available_commands

    def set_mock_result(self, cmd: str, result: CommandResult) -> None:
        """モック結果を設定"""
        self.mock_results[cmd] = result

    def set_available_command(self, command: str) -> None:
        """利用可能なコマンドを設定"""
        self.available_commands.add(command)

    def get_executed_commands(self) -> List[Dict[str, Any]]:
        """実行されたコマンドのリストを取得"""
        return self.executed_commands.copy()


def create_command_executor(mock: bool = False) -> CommandExecutor:
    """CommandExecutorのファクトリ関数

    Args:
        mock: モック実装を使用するか

    Returns:
        CommandExecutor: コマンド実行インスタンス
    """
    if mock:
        return MockCommandExecutor()
    return SubprocessCommandExecutor()
