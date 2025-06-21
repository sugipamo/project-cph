#!/usr/bin/env python3
"""
print使用チェッカー - loggingディレクトリ配下を除く
"""

import glob
import re
from typing import List

from infrastructure.file_handler import FileHandler
from infrastructure.logger import Logger


class PrintUsageChecker:
    def __init__(self, file_handler: FileHandler, logger: Logger, issues: List[str], verbose: bool = False):
        self.file_handler = file_handler
        self.logger = logger
        self.issues = issues
        self.verbose = verbose

    def check_print_usage(self) -> bool:
        """print使用チェック - loggingディレクトリ配下を除く"""
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
            spinner = ProgressSpinner("print使用チェック", self.logger)
            spinner.start()

        print_issues = []

        # print( パターンを検索（コメント除く）
        print_pattern = re.compile(r'\bprint\s*\(')
        comment_pattern = re.compile(r'#.*$')

        for file_path in glob.glob('src/**/*.py', recursive=True):
            # loggingディレクトリ配下は除外
            if '/logging/' in file_path:
                continue

            try:
                content = self.file_handler.read_text(file_path, encoding='utf-8')
                lines = content.splitlines(keepends=True)

                for line_num, line in enumerate(lines, 1):
                    # コメントを除去
                    clean_line = comment_pattern.sub('', line)

                    # print( パターンをチェック
                    if print_pattern.search(clean_line):
                        # file=sys.stderrを使用している場合は許可
                        if 'file=sys.stderr' in clean_line:
                            continue
                        relative_path = file_path.replace('src/', '')
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
