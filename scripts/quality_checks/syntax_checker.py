#!/usr/bin/env python3
"""
構文チェッカー
"""

import ast
from typing import List

from infrastructure.file_handler import FileHandler
from infrastructure.logger import Logger

from .base.base_quality_checker import QualityCheckExecutor


class SyntaxChecker(QualityCheckExecutor):
    def __init__(self, file_handler: FileHandler, logger: Logger, issues: List[str], verbose: bool = False):
        super().__init__(file_handler, logger, issues, verbose)

    def check_syntax(self) -> bool:
        """基本構文チェック（互換性維持用メソッド）"""
        return self.check()

    def check(self) -> bool:
        """基本構文チェック"""
        spinner = None
        if not self.verbose:
            spinner = self.create_progress_spinner("構文チェック")
            spinner.start()

        syntax_errors = []
        target_files = self.get_target_files(excluded_categories=["tests"])

        for file_path in target_files:
            try:
                content = self.file_handler.read_text(file_path, encoding='utf-8')
                ast.parse(content, filename=file_path)
            except SyntaxError as e:
                syntax_errors.append(f'{file_path}:{e.lineno}: {e.msg}')
            except (FileNotFoundError, UnicodeDecodeError, OSError):
                # ファイルが見つからない場合やエンコーディングエラーはスキップ
                continue

        success = len(syntax_errors) == 0

        if spinner:
            spinner.stop(success)
        elif self.verbose:
            self.logger.info(f"{'✅' if success else '❌'} 構文チェック")

        if syntax_errors:
            self.issues.extend(syntax_errors)
            return False
        return True
