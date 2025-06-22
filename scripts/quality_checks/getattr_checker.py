#!/usr/bin/env python3
"""
getattr()デフォルト値使用チェッカー - CLAUDE.md準拠性検知
"""

import ast
from typing import List

from infrastructure.file_handler import FileHandler
from infrastructure.logger import Logger

from .base.base_quality_checker import BaseQualityChecker


class GetattrChecker(BaseQualityChecker):
    def __init__(self, file_handler: FileHandler, logger: Logger, issues: List[str], verbose: bool = False):
        super().__init__(file_handler, logger, issues, verbose)

    def check_getattr_usage(self) -> bool:
        """getattr()デフォルト値使用チェック - CLAUDE.md準拠性違反検知（互換性維持用メソッド）"""
        return self.check()

    def check(self) -> bool:
        """getattr()デフォルト値使用チェック - CLAUDE.md準拠性違反検知"""
        spinner = None
        if not self.verbose:
            spinner = self.create_progress_spinner("getattr()デフォルト値使用チェック")
            spinner.start()

        getattr_issues = []

        # 対象ファイルを設定ベースで取得（testディレクトリを除外）
        target_files = self.get_target_files(excluded_categories=["tests"])

        for file_path in target_files:
            try:
                content = self.file_handler.read_text(file_path, encoding='utf-8')
                tree = ast.parse(content, filename=file_path)
                relative_path = self.get_relative_path(file_path)

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
