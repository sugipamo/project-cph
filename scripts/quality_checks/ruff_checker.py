#!/usr/bin/env python3
"""
Ruffによるコード品質チェッカー
"""

from typing import List, Tuple

from infrastructure.command_executor import CommandExecutor
from infrastructure.file_handler import FileHandler
from infrastructure.logger import Logger


class RuffChecker:
    def __init__(self, command_executor: CommandExecutor, file_handler: FileHandler, logger: Logger, issues: List[str]):
        self.command_executor = command_executor
        self.file_handler = file_handler
        self.logger = logger
        self.issues = issues

    def check_ruff(self) -> bool:
        """Ruffによるコード品質チェック"""
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

        # まず修正可能な問題を自動修正
        spinner1 = ProgressSpinner("Ruff自動修正", self.logger)
        spinner1.start()
        self._run_command(
            ["ruff", "check", "--fix", "--unsafe-fixes", ".", "--exclude", "tests/", "--exclude", "test_results/"],
            "Ruff自動修正"
        )
        spinner1.stop(True)

        # 残った問題をチェック
        spinner2 = ProgressSpinner("コード品質チェック (ruff)", self.logger)
        spinner2.start()
        success, output = self._run_command(
            ["ruff", "check", ".", "--exclude", "tests/", "--exclude", "test_results/"],
            "コード品質チェック (ruff)"
        )
        spinner2.stop(success)

        return success

    def check_quality_scripts(self) -> bool:
        """品質チェックスクリプトを実行"""
        all_passed = True

        # 汎用名チェック
        if self.file_handler.exists("scripts/quality/check_generic_names.py"):
            success, output = self._run_command(
                ["python3", "scripts/quality/check_generic_names.py", "src/"],
                "汎用名チェック"
            )
            all_passed = all_passed and success

        # 実用的品質チェック
        if self.file_handler.exists("scripts/quality/practical_quality_check.py"):
            success, output = self._run_command(
                ["python3", "scripts/quality/practical_quality_check.py"],
                "実用的品質チェック"
            )
            all_passed = all_passed and success
        elif self.file_handler.exists("scripts/quality/functional_quality_check.py"):
            success, output = self._run_command(
                ["python3", "scripts/quality/functional_quality_check.py", "src/"],
                "関数型品質チェック"
            )
            all_passed = all_passed and success

        # アーキテクチャ品質チェック
        if self.file_handler.exists("scripts/quality/architecture_quality_check.py"):
            success, output = self._run_command(
                ["python3", "scripts/quality/architecture_quality_check.py", "src/"],
                "アーキテクチャ品質チェック"
            )
            all_passed = all_passed and success

        return all_passed

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
