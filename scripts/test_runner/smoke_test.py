#!/usr/bin/env python3
"""
スモークテスト - 基本的な実行可能性をチェック
"""

from pathlib import Path
from typing import List

from infrastructure.command_executor import CommandExecutor
from infrastructure.logger import Logger


class SmokeTest:
    def __init__(self, command_executor: CommandExecutor, logger: Logger, issues: List[str], verbose: bool = False):
        self.command_executor = command_executor
        self.logger = logger
        self.issues = issues
        self.verbose = verbose

    def quick_smoke_test(self) -> bool:
        """クイックスモークテスト - 基本的な実行可能性をチェック"""
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

        spinner = None
        if not self.verbose:
            spinner = ProgressSpinner("クイックスモークテスト", self.logger)
            spinner.start()

        # メインモジュールのインポートテスト
        result = self.command_executor.run(
            cmd=[
                "python3", "-c",
                "import sys; sys.path.insert(0, '.'); "
                "from src.main import main; print('OK')"
            ],
            capture_output=True,
            text=True,
            cwd=str(Path(__file__).parent.parent.parent),
            timeout=None,
            env=None,
            check=False
        )

        success = result.success

        if spinner:
            spinner.stop(success)
        elif self.verbose:
            self.logger.info(f"{'✅' if success else '❌'} クイックスモークテスト")

        if not success:
            error_output = result.stderr.strip() or result.stdout.strip() or f"終了コード: {result.returncode}"
            self.issues.append(f"スモークテスト失敗: {error_output}")

        return success
