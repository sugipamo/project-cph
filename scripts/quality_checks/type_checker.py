#!/usr/bin/env python3
"""
型チェッカー (mypy)
"""

from pathlib import Path
from typing import List, Tuple

from infrastructure.command_executor import CommandExecutor
from infrastructure.file_handler import FileHandler
from infrastructure.logger import Logger

from .base.base_quality_checker import BaseQualityChecker


class TypeChecker(BaseQualityChecker):
    def __init__(self, file_handler: FileHandler, command_executor: CommandExecutor, logger: Logger, issues: List[str], verbose: bool = False):
        super().__init__(file_handler, logger, issues, verbose)
        self.command_executor = command_executor

    def check_types(self) -> bool:
        """型チェック（互換性維持用メソッド）"""
        return self.check()

    def check(self) -> bool:
        """型チェック (mypy)"""
        spinner = None
        if not self.verbose:
            spinner = self.create_progress_spinner("型チェック")
            spinner.start()

        # mypyが利用可能かチェック
        result = self.command_executor.run(
            cmd=["python3", "-m", "mypy", "--version"],
            capture_output=True,
            text=True,
            cwd=None,
            timeout=None,
            env=None,
            check=False
        )
        if not result.success:
            error_msg = "mypyの実行に失敗しました"
            self.logger.error(error_msg)
            self.issues.append(error_msg)
            if spinner:
                spinner.stop(False)
            return False

        # 対象ディレクトリを設定ベースで取得
        target_directories = self.config.get_target_directories()

        success = True
        for target_dir in target_directories:
            # mypy実行と結果分析
            dir_success, output = self._run_command(
                ["python3", "-m", "mypy", f"{target_dir}/", "--no-error-summary"],
                f"型チェック ({target_dir})"
            )

            if not dir_success:
                success = False
                if output:
                    self._analyze_type_errors(output)

        if spinner:
            spinner.stop(success)
        elif self.verbose:
            self.logger.info(f"{'✅' if success else '❌'} 型チェック")

        return success

    def _run_command(self, cmd: List[str], description: str) -> Tuple[bool, str]:
        """コマンドを実行し、結果を返す"""
        result = self.command_executor.run(
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

    def _analyze_type_errors(self, output: str) -> None:
        """型エラー分析（簡潔なサマリーを表示）"""
        lines = output.split('\n')
        type_errors = []
        error_by_file = {}

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # mypyエラー行のパターン: "[src|scripts]/path/file.py:line:col: error: message [error-code]"
            is_target_file = any(line.startswith(f'{target_dir}/') for target_dir in self.config.get_target_directories())
            if is_target_file and ': error:' in line:
                parts = line.split(': error:', 1)
                if len(parts) == 2:
                    file_location = parts[0]
                    error_message = parts[1].strip()

                    # ファイルパスとエラーメッセージを抽出
                    if ':' in file_location:
                        file_path = file_location.split(':')[0]
                        short_path = self.get_relative_path(file_path)

                        if short_path not in error_by_file:
                            error_by_file[short_path] = 0
                        error_by_file[short_path] += 1

                        # 重要なエラーのみ詳細表示
                        if self._is_important_type_error(error_message):
                            type_errors.append(f"{short_path}: {error_message}")

        if type_errors or error_by_file:
            # ファイル別エラー数サマリー
            if error_by_file:
                total_errors = sum(error_by_file.values())
                error_files = len(error_by_file)
                self.issues.append(f"型エラー: {total_errors}件 ({error_files}ファイル)")

                # エラー数の多いファイルを表示（上位10件）
                sorted_files = sorted(error_by_file.items(), key=lambda x: x[1], reverse=True)
                self.issues.append("エラー数の多いファイル:")
                for file_path, count in sorted_files[:10]:
                    self.issues.append(f"  {file_path}: {count}件")

                if len(sorted_files) > 10:
                    self.issues.append(f"  ... 他{len(sorted_files) - 10}ファイル")

            # 重要なエラーの詳細表示（最大5件）
            if type_errors:
                self.issues.append("主要な型エラー:")
                for error in type_errors[:5]:
                    self.issues.append(f"  {error}")

                if len(type_errors) > 5:
                    self.issues.append(f"  ... 他{len(type_errors) - 5}件")

    def _is_important_type_error(self, error_message: str) -> bool:
        """重要な型エラーかどうかを判定"""
        important_patterns = [
            'has no attribute',
            'incompatible type',
            'cannot be assigned',
            'is not subscriptable',
            'missing type annotation',
            'no-untyped-def',
            'arg-type'
        ]

        return any(pattern in error_message.lower() for pattern in important_patterns)
