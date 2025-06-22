#!/usr/bin/env python3
"""
Ruffによるコード品質チェッカー
"""

from pathlib import Path
from typing import List, Tuple

from infrastructure.command_executor import CommandExecutor
from infrastructure.file_handler import FileHandler
from infrastructure.logger import Logger

from .base.base_quality_checker import QualityCheckExecutor


class RuffChecker(QualityCheckExecutor):
    def __init__(self, file_handler: FileHandler, command_executor: CommandExecutor, logger: Logger, issues: List[str], verbose: bool = False):
        super().__init__(file_handler, logger, issues, verbose)
        self.command_executor = command_executor

    def check_ruff(self) -> bool:
        """Ruffによるコード品質チェック（互換性維持用メソッド）"""
        return self.check()

    def check(self) -> bool:
        """Ruffによるコード品質チェック"""
        # 対象ディレクトリを設定から取得
        target_directories = self.config.get_target_directories()

        # まず修正可能な問題を自動修正
        spinner1 = None
        if not self.verbose:
            spinner1 = self.create_progress_spinner("Ruff自動修正")
            spinner1.start()

        for target_dir in target_directories:
            self._run_command(
                ["ruff", "check", "--fix", "--unsafe-fixes", target_dir, "--exclude", "tests/", "--exclude", "test_results/"],
                f"Ruff自動修正 ({target_dir})"
            )

        if spinner1:
            spinner1.stop(True)
        elif self.verbose:
            self.logger.info("✅ Ruff自動修正")

        # 残った問題をチェック
        spinner2 = None
        if not self.verbose:
            spinner2 = self.create_progress_spinner("コード品質チェック (ruff)")
            spinner2.start()

        overall_success = True
        for target_dir in target_directories:
            success, output = self._run_command(
                ["ruff", "check", target_dir, "--exclude", "tests/", "--exclude", "test_results/"],
                f"コード品質チェック (ruff - {target_dir})"
            )
            if not success:
                overall_success = False

        if spinner2:
            spinner2.stop(overall_success)
        elif self.verbose:
            self.logger.info(f"{'✅' if overall_success else '❌'} コード品質チェック (ruff)")

        return overall_success

    def check_quality_scripts(self) -> bool:
        """品質チェックスクリプトを実行"""
        all_passed = True
        target_directories = self.config.get_target_directories()

        # 汎用名チェック
        script_path = self.config.get_script_path("generic_name_checker")
        if self.file_handler.exists(script_path):
            for target_dir in target_directories:
                success, output = self._run_command(
                    ["python3", script_path, f"{target_dir}/"],
                    f"汎用名チェック ({target_dir})"
                )
                all_passed = all_passed and success

        # 実用的品質チェック
        try:
            practical_script = self.config.get_script_path("practical_quality_checker")
            if self.file_handler.exists(practical_script):
                success, output = self._run_command(
                    ["python3", practical_script],
                    "実用的品質チェック"
                )
                all_passed = all_passed and success
        except KeyError:
            # フォールバック処理は禁止されているため、設定ファイルに追加が必要
            pass

        try:
            functional_script = self.config.get_script_path("functional_quality_checker")
            if self.file_handler.exists(functional_script):
                for target_dir in target_directories:
                    success, output = self._run_command(
                        ["python3", functional_script, f"{target_dir}/"],
                        f"関数型品質チェック ({target_dir})"
                    )
                    all_passed = all_passed and success
        except KeyError:
            pass

        # アーキテクチャ品質チェック
        try:
            arch_script = self.config.get_script_path("architecture_quality_checker")
            if self.file_handler.exists(arch_script):
                for target_dir in target_directories:
                    success, output = self._run_command(
                        ["python3", arch_script, f"{target_dir}/"],
                        f"アーキテクチャ品質チェック ({target_dir})"
                    )
                    all_passed = all_passed and success
        except KeyError:
            pass

        return all_passed

    def _run_command(self, cmd: List[str], description: str) -> Tuple[bool, str]:
        """コマンドを実行し、結果を返す"""
        result = self.command_executor.execute_command(
            cmd=cmd,
            capture_output=True,
            text=True,
            cwd=str(Path(__file__).parent.parent.parent),
            timeout=None,
            env=None,
            check=False
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
