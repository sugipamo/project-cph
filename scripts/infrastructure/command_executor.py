"""外部コマンド実行の抽象化と実装

Scripts配下で2番目に重要な副作用であるsubprocess.runを
依存性注入可能な形で抽象化
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Union

from .subprocess_wrapper import SubprocessWrapper


@dataclass
class CommandResult:
    """コマンド実行結果"""
    returncode: int
    stdout: str
    stderr: str
    success: bool

    @classmethod
    def from_process_result(cls, result) -> 'CommandResult':
        """ProcessResultから変換"""
        return cls(
            returncode=result.returncode,
            stdout=result.stdout or "",
            stderr=result.stderr or "",
            success=result.returncode == 0
        )


class CommandExecutor(ABC):
    """コマンド実行インターフェース"""

    @abstractmethod
    def execute_command(
        self,
        cmd: Union[List[str], str],
        capture_output: bool,
        text: bool,
        cwd: Optional[str],
        timeout: Optional[float],
        env: Optional[Dict[str, str]],
        check: bool
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

    @abstractmethod
    def execute_command_with_live_output(
        self,
        cmd: Union[List[str], str],
        output_callback: callable,
        cwd: Optional[str],
        timeout: Optional[float],
        env: Optional[Dict[str, str]]
    ) -> CommandResult:
        """コマンドを実行してリアルタイムで出力を処理

        Args:
            cmd: 実行するコマンド
            output_callback: 出力行を受け取るコールバック関数
            cwd: 作業ディレクトリ
            timeout: タイムアウト（秒）
            env: 環境変数

        Returns:
            CommandResult: 実行結果
        """
        pass


class SubprocessCommandExecutor(CommandExecutor):
    """SubprocessWrapperを使用した実装"""

    def __init__(self, subprocess_wrapper: SubprocessWrapper):
        self._subprocess = subprocess_wrapper

    def execute_command(
        self,
        cmd: Union[List[str], str],
        capture_output: bool,
        text: bool,
        cwd: Optional[str],
        timeout: Optional[float],
        env: Optional[Dict[str, str]],
        check: bool
    ) -> CommandResult:
        """SubprocessWrapperを使用してコマンドを実行"""
        from .subprocess_wrapper import CalledProcessError, TimeoutExpiredError

        try:
            result = self._subprocess.run(
                cmd,
                capture_output=capture_output,
                text=text,
                cwd=cwd,
                timeout=timeout,
                env=env,
                check=check,
                shell=False
            )
            return CommandResult.from_process_result(result)
        except CalledProcessError as e:
            return CommandResult(
                returncode=e.returncode,
                stdout=e.output or "",
                stderr=e.stderr or "",
                success=False
            )
        except TimeoutExpiredError as e:
            return CommandResult(
                returncode=-1,
                stdout=e.output or "",
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
        from .subprocess_wrapper import CalledProcessError, TimeoutExpiredError

        try:
            result = self._subprocess.run(
                [command, "--version"],
                capture_output=True,
                text=True,
                timeout=10,
                env=None,
                check=False,
                shell=False
            )
            return result.returncode == 0
        except (CalledProcessError, FileNotFoundError, TimeoutExpiredError):
            try:
                # --versionが使えない場合は-hを試す
                result = self._subprocess.run(
                    [command, "-h"],
                    capture_output=True,
                    text=True,
                    timeout=10,
                    env=None,
                    check=False,
                    shell=False
                )
                return result.returncode == 0
            except (CalledProcessError, FileNotFoundError, TimeoutExpiredError) as e:
                raise RuntimeError(f"コマンド利用可能性チェックに失敗: {command}, エラー: {e}") from e

    def execute_command_with_live_output(
        self,
        cmd: Union[List[str], str],
        output_callback: callable,
        cwd: Optional[str],
        timeout: Optional[float],
        env: Optional[Dict[str, str]]
    ) -> CommandResult:
        """SubprocessWrapperを使用してリアルタイムで出力を処理"""
        import threading

        from .subprocess_wrapper import TimeoutExpiredError

        try:
            # コマンドをリスト形式に統一
            if isinstance(cmd, str):
                cmd = cmd.split()

            # プロセスを開始
            process = self._subprocess.popen(
                cmd,
                stdout=self._subprocess.PIPE,
                stderr=self._subprocess.STDOUT,  # stderrもstdoutにリダイレクト
                text=True,
                cwd=cwd,
                env=env,
                bufsize=1,  # 行バッファリング
                universal_newlines=True
            )

            stdout_lines = []

            def read_output():
                """出力を読み込んでコールバックを呼び出す"""
                try:
                    for line in iter(process.stdout.readline, ''):
                        if line:
                            line = line.rstrip('\n\r')
                            stdout_lines.append(line)
                            output_callback(line)
                except Exception:
                    pass
                finally:
                    if hasattr(process.stdout, 'close'):
                        process.stdout.close()

            # 出力読み込みスレッドを開始
            output_thread = threading.Thread(target=read_output)
            output_thread.daemon = True
            output_thread.start()

            # プロセスの完了を待機
            try:
                returncode = process.wait(timeout=timeout)
            except TimeoutExpiredError as e:
                process.kill()
                raise TimeoutExpiredError(cmd=cmd, timeout=timeout, output=None, stderr=None) from e

            # 出力スレッドの完了を待機
            output_thread.join(timeout=1.0)

            return CommandResult(
                returncode=returncode,
                stdout='\n'.join(stdout_lines),
                stderr="",
                success=returncode == 0
            )

        except FileNotFoundError as e:
            return CommandResult(
                returncode=-1,
                stdout="",
                stderr=f"Command not found: {e}",
                success=False
            )
        except Exception as e:
            return CommandResult(
                returncode=-1,
                stdout="",
                stderr=f"Execution error: {e}",
                success=False
            )


class MockCommandExecutor(CommandExecutor):
    """テスト用のモック実装"""

    def __init__(self):
        self.executed_commands: List[Dict[str, Any]] = []
        self.mock_results: Dict[str, CommandResult] = {}
        self.available_commands: set = set()

    def execute_command(
        self,
        cmd: Union[List[str], str],
        capture_output: bool,
        text: bool,
        cwd: Optional[str],
        timeout: Optional[float],
        env: Optional[Dict[str, str]],
        check: bool
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

    def execute_command_with_live_output(
        self,
        cmd: Union[List[str], str],
        output_callback: callable,
        cwd: Optional[str],
        timeout: Optional[float],
        env: Optional[Dict[str, str]]
    ) -> CommandResult:
        """モックライブ出力実行"""
        # 実行されたコマンドを記録
        self.executed_commands.append({
            'cmd': cmd,
            'output_callback': output_callback,
            'cwd': cwd,
            'timeout': timeout,
            'env': env
        })

        # モック出力をコールバックに送信
        import time
        mock_lines = [
            "Mock test line 1",
            "Mock test line 2",
            "Mock test line 3"
        ]

        for line in mock_lines:
            output_callback(line)
            time.sleep(0.1)

        # デフォルトは成功
        return CommandResult(
            returncode=0,
            stdout="\n".join(mock_lines),
            stderr="",
            success=True
        )


def create_command_executor(mock: bool, subprocess_wrapper: Optional[SubprocessWrapper]) -> CommandExecutor:
    """CommandExecutorのファクトリ関数

    Args:
        mock: モック実装を使用するか
        subprocess_wrapper: SubprocessWrapperの実装（省略時は実装を作成）

    Returns:
        CommandExecutor: コマンド実行インスタンス
    """
    if mock:
        return MockCommandExecutor()

    if subprocess_wrapper is None:
        from .subprocess_impl import SubprocessWrapperImpl
        subprocess_wrapper = SubprocessWrapperImpl()

    return SubprocessCommandExecutor(subprocess_wrapper)
