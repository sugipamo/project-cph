#!/usr/bin/env python3
"""
構文チェッカー
"""

import ast
import glob
from typing import List

from infrastructure.file_handler import FileHandler
from infrastructure.logger import Logger


class SyntaxChecker:
    def __init__(self, file_handler: FileHandler, logger: Logger, issues: List[str], verbose: bool = False):
        self.file_handler = file_handler
        self.logger = logger
        self.issues = issues
        self.verbose = verbose

    def check_syntax(self) -> bool:
        """基本構文チェック"""
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
            spinner = ProgressSpinner("構文チェック", self.logger)
            spinner.start()

        syntax_errors = []
        for file_path in glob.glob('src/**/*.py', recursive=True):
            try:
                content = self.file_handler.read_text(file_path, encoding='utf-8')
                ast.parse(content, filename=file_path)
            except SyntaxError as e:
                syntax_errors.append(f'{file_path}:{e.lineno}: {e.msg}')
            except FileNotFoundError:
                # ファイルが見つからない場合はスキップ
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
