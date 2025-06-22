#!/usr/bin/env python3
"""
getattr()デフォルト値使用チェッカー - CLAUDE.md準拠性検知
"""

import ast
import glob
from typing import List

from infrastructure.file_handler import FileHandler
from infrastructure.logger import Logger


class GetattrChecker:
    def __init__(self, file_handler: FileHandler, logger: Logger, issues: List[str], verbose: bool = False):
        self.file_handler = file_handler
        self.logger = logger
        self.issues = issues
        self.verbose = verbose

    def check_getattr_usage(self) -> bool:
        """getattr()デフォルト値使用チェック - CLAUDE.md準拠性違反検知"""
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
            spinner = ProgressSpinner("getattr()デフォルト値使用チェック", self.logger)
            spinner.start()

        getattr_issues = []

        for file_path in glob.glob('src/**/*.py', recursive=True):
            # テストファイルは除外
            if '/tests/' in file_path:
                continue

            try:
                content = self.file_handler.read_text(file_path, encoding='utf-8')
                tree = ast.parse(content, filename=file_path)
                relative_path = file_path.replace('src/', '')

                # AST解析によるgetattr()デフォルト値使用検出
                for node in ast.walk(tree):
                    if (isinstance(node, ast.Call) and
                        isinstance(node.func, ast.Name) and
                        node.func.id == 'getattr' and
                        len(node.args) >= 3):
                        # getattr(obj, 'attr', default) パターンを検出
                        context_line = self._get_source_line(content, node.lineno)
                        getattr_issues.append(f"{relative_path}:{node.lineno} {context_line.strip()}")

            except (SyntaxError, UnicodeDecodeError, OSError, FileNotFoundError):
                # 構文エラーやファイル読み込みエラーは無視
                continue

        success = len(getattr_issues) == 0

        if spinner:
            spinner.stop(success)
        elif self.verbose:
            self.logger.info(f"{'✅' if success else '❌'} getattr()デフォルト値使用チェック")

        if getattr_issues:
            self.issues.append("getattr()のデフォルト値使用が検出されました（CLAUDE.md準拠性違反）:")
            for issue in getattr_issues[:20]:  # 最大20件表示
                self.issues.append(f"  {issue}")

            if len(getattr_issues) > 20:
                self.issues.append(f"  ... 他{len(getattr_issues) - 20}件")

            return False

        return success

    def _get_source_line(self, content: str, line_num: int) -> str:
        """指定行のソースコードを取得"""
        lines = content.splitlines()
        if 1 <= line_num <= len(lines):
            return lines[line_num - 1]
        return ""
