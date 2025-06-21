#!/usr/bin/env python3
"""
未使用コード検出 (vulture)
"""

from typing import List, Tuple

from infrastructure.command_executor import CommandExecutor
from infrastructure.logger import Logger


class DeadCodeChecker:
    def __init__(self, command_executor: CommandExecutor, logger: Logger, warnings: List[str], issues: List[str]):
        self.command_executor = command_executor
        self.logger = logger
        self.warnings = warnings
        self.issues = issues

    def check_dead_code(self) -> bool:
        """vultureを使用した未使用コード検出"""
        # ProgressSpinnerクラスを直接定義
        from infrastructure.logger import Logger

        class ProgressSpinner:
            def __init__(self, message: str, logger: Logger):
                self.message = message
                self.logger = logger

            def start(self):
                pass  # チェック中表示は不要

            def stop(self, success: bool = True):
                self.logger.info(f"{'✅' if success else '❌'} {self.message}")

        # vultureが利用可能かチェック
        result = self.command_executor.run(["vulture", "--version"], capture_output=True, text=True)
        if not result.success:
            error_msg = "vultureの実行に失敗しました"
            self.logger.error(error_msg)
            self.issues.append(error_msg)
            return False

        spinner = ProgressSpinner("未使用コード検出", self.logger)
        spinner.start()

        success, output = self._run_command(
            ["vulture", "src/", ".vulture_whitelist.py", "--min-confidence", "80"],
            "未使用コード検出"
        )

        # 未使用コードが検出された場合は警告として扱う（エラーではない）
        # vultureは未使用コード検出時に終了コード1を返すが、標準出力に結果があれば正常
        if output.strip():
            # 出力を解析して警告として追加
            dead_code_lines = [line.strip() for line in output.strip().split('\n') if line.strip()]
            if dead_code_lines:
                self.warnings.append("未使用コードが検出されました:")
                for line in dead_code_lines[:10]:  # 最大10件表示
                    # ファイルパスを短縮表示
                    if line.startswith('src/'):
                        line = line[4:]  # 'src/'を除去
                    self.warnings.append(f"  {line}")

                if len(dead_code_lines) > 10:
                    self.warnings.append(f"  ... 他{len(dead_code_lines) - 10}件")

        spinner.stop(True)
        return True  # 警告レベルなので常にTrueを返す

    def _run_command(self, cmd: List[str], description: str) -> Tuple[bool, str]:
        """コマンドを実行し、結果を返す"""
        from pathlib import Path

        result = self.command_executor.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=str(Path(__file__).parent.parent.parent)
        )

        success = result.success

        # vultureの場合は特別処理（未使用コード検出時は正常終了とみなす）
        if cmd[0] == "vulture" and result.stdout.strip():
            return True, result.stdout

        if not success:
            combined_output = ""
            if result.stdout.strip():
                combined_output += result.stdout.strip()
            if result.stderr.strip():
                if combined_output:
                    combined_output += "\n"
                combined_output += result.stderr.strip()

            if not combined_output:
                combined_output = f"終了コード: {result.returncode}"

            self.issues.append(f"{description}: {combined_output}")
            return False, combined_output

        return True, result.stdout
