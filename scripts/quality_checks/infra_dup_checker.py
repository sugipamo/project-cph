#!/usr/bin/env python3
"""
Infrastructure重複生成チェッカー - main.py以外での生成禁止
"""

import ast
from typing import List

from infrastructure.file_handler import FileHandler
from infrastructure.logger import Logger

from .base.base_quality_checker import QualityCheckExecutor


class InfrastructureDuplicationChecker(QualityCheckExecutor):
    def __init__(self, file_handler: FileHandler, logger: Logger, issues: List[str], verbose: bool = False):
        super().__init__(file_handler, logger, issues, verbose)

    def check_infrastructure_duplication(self) -> bool:
        """Infrastructure重複生成の検出（CLAUDE.mdルール違反 - main.py以外での生成禁止）（互換性維持用メソッド）"""
        return self.check()

    def check(self) -> bool:
        """Infrastructure重複生成の検出（CLAUDE.mdルール違反 - main.py以外での生成禁止）"""
        spinner = None
        if not self.verbose:
            spinner = self.create_progress_spinner("Infrastructure重複生成チェック")
            spinner.start()

        duplication_issues = []

        # 対象ファイルを設定ベースで取得（main.pyとtestディレクトリを除外）
        target_files = self.get_target_files(excluded_categories=["tests"])

        for file_path in target_files:
            # main.pyは除外
            if file_path.endswith('/main.py') or file_path.endswith('main.py'):
                continue

            try:
                content = self.file_handler.read_text(file_path, encoding='utf-8')
                tree = ast.parse(content, filename=file_path)
                relative_path = self.get_relative_path(file_path)

                # build_infrastructure()呼び出しを検出
                for node in ast.walk(tree):
                    if isinstance(node, ast.Call):
                        # 直接呼び出し: build_infrastructure()
                        if isinstance(node.func, ast.Name) and node.func.id == 'build_infrastructure':
                            duplication_issues.append(f"{relative_path}:{node.lineno} build_infrastructure() の直接呼び出し")

                        # モジュール経由: module.build_infrastructure()
                        elif isinstance(node.func, ast.Attribute) and node.func.attr == 'build_infrastructure':
                            duplication_issues.append(f"{relative_path}:{node.lineno} {self._get_attr_chain(node.func)} の呼び出し")

                # build_infrastructure のインポートも検出
                for node in ast.walk(tree):
                    if isinstance(node, ast.ImportFrom):
                        if node.module and 'build_infrastructure' in node.module:
                            for alias in node.names or []:
                                if alias.name == 'build_infrastructure':
                                    duplication_issues.append(f"{relative_path}:{node.lineno} build_infrastructure のインポート")
                    elif isinstance(node, ast.Import):
                        for alias in node.names:
                            if 'build_infrastructure' in alias.name:
                                duplication_issues.append(f"{relative_path}:{node.lineno} {alias.name} のインポート")

            except (SyntaxError, UnicodeDecodeError, OSError, FileNotFoundError):
                continue

        success = len(duplication_issues) == 0

        if spinner:
            spinner.stop(success)
        elif self.verbose:
            self.logger.info(f"{'✅' if success else '❌'} Infrastructure重複生成チェック")

        if duplication_issues:
            self.issues.append("Infrastructure重複生成が検出されました（CLAUDE.mdルール違反 - すべてmain.pyから注入する）:")
            for issue in duplication_issues:
                self.issues.append(f"  {issue}")

        return success

    def _get_attr_chain(self, node: ast.Attribute) -> str:
        """属性チェーンを文字列として取得"""
        if isinstance(node.value, ast.Name):
            return f"{node.value.id}.{node.attr}"
        if isinstance(node.value, ast.Attribute):
            return f"{self._get_attr_chain(node.value)}.{node.attr}"
        return f"<expr>.{node.attr}"
