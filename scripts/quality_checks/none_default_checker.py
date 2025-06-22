#!/usr/bin/env python3
"""
None引数初期値チェッカー - デフォルト値使用禁止
"""

import ast
from typing import List

from infrastructure.file_handler import FileHandler
from infrastructure.logger import Logger

from .base.base_quality_checker import BaseQualityChecker


class NoneDefaultChecker(BaseQualityChecker):
    def __init__(self, file_handler: FileHandler, logger: Logger, issues: List[str], verbose: bool = False):
        super().__init__(file_handler, logger, issues, verbose)

    def check_none_default_arguments(self) -> bool:
        """None引数初期値の検出（CLAUDE.mdルール違反 - デフォルト値使用禁止）（互換性維持用メソッド）"""
        return self.check()

    def check(self) -> bool:
        """None引数初期値の検出（CLAUDE.mdルール違反 - デフォルト値使用禁止）"""
        spinner = None
        if not self.verbose:
            spinner = self.create_progress_spinner("None引数初期値チェック")
            spinner.start()

        none_default_issues = []

        # Infrastructure層を除外した対象ファイルを設定ベースで取得
        target_files = self.get_target_files(excluded_categories=["infrastructure", "tests"])

        for file_path in target_files:
            try:
                content = self.file_handler.read_text(file_path, encoding='utf-8')
                tree = ast.parse(content, filename=file_path)
                relative_path = self.get_relative_path(file_path)

                for node in ast.walk(tree):
                    # 関数定義での引数チェック
                    if isinstance(node, ast.FunctionDef):
                        # 正当なNoneデフォルト値のパターンを除外
                        if self._is_legitimate_none_default(node.name, relative_path):
                            continue
                        for arg in node.args.defaults:
                            if isinstance(arg, ast.Constant) and arg.value is None:
                                none_default_issues.append(f"{relative_path}:{node.lineno} def {node.name} - None引数初期値")

                        # キーワード専用引数のデフォルト値もチェック
                        for arg in node.args.kw_defaults:
                            if arg is not None and isinstance(arg, ast.Constant) and arg.value is None:
                                none_default_issues.append(f"{relative_path}:{node.lineno} def {node.name} - キーワード引数のNone初期値")

                    # 非同期関数定義での引数チェック
                    elif isinstance(node, ast.AsyncFunctionDef):
                        for arg in node.args.defaults:
                            if isinstance(arg, ast.Constant) and arg.value is None:
                                none_default_issues.append(f"{relative_path}:{node.lineno} async def {node.name} - None引数初期値")

                        # キーワード専用引数のデフォルト値もチェック
                        for arg in node.args.kw_defaults:
                            if arg is not None and isinstance(arg, ast.Constant) and arg.value is None:
                                none_default_issues.append(f"{relative_path}:{node.lineno} async def {node.name} - キーワード引数のNone初期値")

            except (SyntaxError, UnicodeDecodeError, OSError, FileNotFoundError):
                continue

        success = len(none_default_issues) == 0

        if spinner:
            spinner.stop(success)
        elif self.verbose:
            self.logger.info(f"{'✅' if success else '❌'} None引数初期値チェック")

        if none_default_issues:
            self.issues.append("None引数初期値が検出されました（CLAUDE.mdルール違反 - 呼び出し元で適切な値を用意）:")
            for issue in none_default_issues[:25]:
                self.issues.append(f"  {issue}")

            if len(none_default_issues) > 25:
                self.issues.append(f"  ... 他{len(none_default_issues) - 25}件")

        return success

    def _is_legitimate_none_default(self, function_name: str, file_path: str) -> bool:
        """正当なNoneデフォルト値のパターンを判定"""
        # Exception classes and factory classes often need None defaults
        legitimate_functions = ['__init__', 'main']
        legitimate_file_patterns = [
            'exception', 'factory', 'cli_app', 'request', 'base_',
            'persistence_', 'composite_'
        ]

        if function_name in legitimate_functions:
            return any(pattern in file_path.lower() for pattern in legitimate_file_patterns)

        # Other specific function patterns that may need None defaults
        function_patterns = ['_execute_core', 'is_potential_script_path']
        return function_name in function_patterns
