#!/usr/bin/env python3
"""
print使用チェッカー - loggingディレクトリ配下を除く
"""

import re
from typing import List

from infrastructure.file_handler import FileHandler
from infrastructure.logger import Logger

from .base.base_quality_checker import QualityCheckExecutor


class PrintUsageChecker(QualityCheckExecutor):
    def __init__(self, file_handler: FileHandler, logger: Logger, issues: List[str], verbose: bool = False):
        super().__init__(file_handler, logger, issues, verbose)

    def check_print_usage(self) -> bool:
        """print使用チェック - loggingディレクトリ配下を除く（互換性維持用メソッド）"""
        return self.check()

    def check(self) -> bool:
        """print使用チェック - loggingディレクトリ配下を除く"""
        spinner = None
        if not self.verbose:
            spinner = self.create_progress_spinner("print使用チェック")
            spinner.start()

        print_issues = []

        # print( パターンを検索（コメント除く）
        print_pattern = re.compile(r'\bprint\s*\(')
        comment_pattern = re.compile(r'#.*$')

        # loggingディレクトリを除外した対象ファイルを設定ベースで取得
        target_files = self.get_target_files(excluded_categories=["logging", "tests"])

        for file_path in target_files:
            try:
                content = self.file_handler.read_text(file_path, encoding='utf-8')
                lines = content.splitlines(keepends=True)
                relative_path = self.get_relative_path(file_path)

                for line_num, line in enumerate(lines, 1):
                    # コメントを除去
                    clean_line = comment_pattern.sub('', line)

                    # print( パターンをチェック
                    if print_pattern.search(clean_line):
                        # file=sys.stderrを使用している場合は許可
                        if 'file=sys.stderr' in clean_line:
                            continue
                        print_issues.append(f"{relative_path}:{line_num} {clean_line.strip()}")

            except (UnicodeDecodeError, OSError, FileNotFoundError):
                # ファイル読み込みエラーは無視
                continue

        success = len(print_issues) == 0

        if spinner:
            spinner.stop(success)
        elif self.verbose:
            self.logger.info(f"{'✅' if success else '❌'} print使用チェック")

        if print_issues:
            self.issues.append("print()の使用が検出されました（ロギング使用を推奨）:")
            for issue in print_issues[:20]:  # 最大20件表示
                self.issues.append(f"  {issue}")

            if len(print_issues) > 20:
                self.issues.append(f"  ... 他{len(print_issues) - 20}件")

            return False

        return success
