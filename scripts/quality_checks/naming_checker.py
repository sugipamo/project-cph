#!/usr/bin/env python3
"""
命名規則チェッカー
"""

import ast
import re
from pathlib import Path
from typing import List

from infrastructure.file_handler import FileHandler
from infrastructure.logger import Logger

from .base.base_quality_checker import QualityCheckExecutor


class NamingChecker(QualityCheckExecutor):
    def __init__(self, file_handler: FileHandler, logger: Logger, warnings: List[str], verbose: bool = False):
        super().__init__(file_handler, logger, warnings, verbose)

    def check_naming_conventions(self) -> bool:
        """命名規則チェック（互換性維持用メソッド）"""
        return self.check()

    def check(self) -> bool:
        """命名規則チェック"""
        spinner = None
        if not self.verbose:
            spinner = self.create_progress_spinner("命名規則チェック")
            spinner.start()

        naming_issues = []

        # 汎用的すぎるファイル名を検出
        generic_filenames = [
            'helpers.py', 'utils.py', 'core.py', 'base.py', 'common.py',
            'misc.py', 'tools.py', 'generic.py', 'data.py', 'info.py'
        ]

        # 抽象的すぎる関数名パターン
        abstract_function_patterns = [
            r'^handle$', r'^process$', r'^manage$', r'^execute$', r'^create$',
            r'^build$', r'^run$', r'^do_', r'^perform_', r'^get$', r'^set$'
        ]

        # 汎用的すぎるクラス名パターン
        generic_class_patterns = [
            r'^Base[A-Z]', r'^Abstract[A-Z]', r'^Generic[A-Z]',
            r'^Manager$', r'^Handler$', r'^Processor$', r'^Helper$'
        ]

        # 無駄なプレフィックスパターン（ファイル名、関数名用）
        useless_prefix_patterns = [
            r'^simple_', r'^pure_', r'^basic_', r'^plain_', r'^raw_',
            r'^common_', r'^general_', r'^standard_', r'^default_',
            r'^normal_', r'^regular_', r'^typical_', r'^ordinary_'
        ]

        # 無駄なプレフィックスパターン（クラス名用 - キャメルケース）
        useless_class_prefix_patterns = [
            r'^Simple[A-Z]', r'^Pure[A-Z]', r'^Basic[A-Z]', r'^Plain[A-Z]', r'^Raw[A-Z]',
            r'^Common[A-Z]', r'^General[A-Z]', r'^Standard[A-Z]', r'^Default[A-Z]',
            r'^Normal[A-Z]', r'^Regular[A-Z]', r'^Typical[A-Z]', r'^Ordinary[A-Z]'
        ]

        # 対象ファイルを設定ベースで取得（testディレクトリを除外）
        target_files = self.get_target_files(excluded_categories=["tests"])

        for file_path in target_files:
            file_name = Path(file_path).name
            relative_path = self.get_relative_path(file_path)

            # ファイル名チェック
            if file_name in generic_filenames:
                naming_issues.append(f"汎用的ファイル名: {relative_path}")

            # 無駄なプレフィックスファイル名チェック
            base_filename = file_name.replace('.py', '')
            for pattern in useless_prefix_patterns:
                if re.match(pattern, base_filename):
                    naming_issues.append(f"無駄なプレフィックスファイル名: {relative_path}")
                    break

            # 長すぎるファイル名チェック（35文字以上）
            if len(file_name) > 35:
                naming_issues.append(f"長すぎるファイル名: {relative_path} ({len(file_name)}文字)")

            try:
                content = self.file_handler.read_text(file_path, encoding='utf-8')
                tree = ast.parse(content, filename=file_path)

                # クラス名チェック
                for node in ast.walk(tree):
                    if isinstance(node, ast.ClassDef):
                        class_name = node.name
                        # 汎用的クラス名チェック
                        for pattern in generic_class_patterns:
                            if re.match(pattern, class_name):
                                naming_issues.append(f"汎用的クラス名: {relative_path}:{node.lineno} class {class_name}")
                                break
                        # 無駄なプレフィックスクラス名チェック
                        for pattern in useless_class_prefix_patterns:
                            if re.match(pattern, class_name):
                                naming_issues.append(f"無駄なプレフィックスクラス名: {relative_path}:{node.lineno} class {class_name}")
                                break

                    # 関数名チェック
                    elif isinstance(node, ast.FunctionDef):
                        func_name = node.name
                        # プライベートメソッドやspecialメソッドはスキップ
                        if not func_name.startswith('_'):
                            # SQLite互換メソッドの例外処理
                            is_sqlite_compat = (
                                func_name == 'execute' and
                                'sqlite' in relative_path.lower() and
                                'MockSQLiteConnection' in content
                            )

                            if not is_sqlite_compat:
                                # 抽象的関数名チェック
                                for pattern in abstract_function_patterns:
                                    if re.match(pattern, func_name):
                                        naming_issues.append(f"抽象的関数名: {relative_path}:{node.lineno} def {func_name}")
                                        break
                            # 無駄なプレフィックス関数名チェック
                            for pattern in useless_prefix_patterns:
                                if re.match(pattern, func_name):
                                    naming_issues.append(f"無駄なプレフィックス関数名: {relative_path}:{node.lineno} def {func_name}")
                                    break

            except SyntaxError:
                # 構文エラーのファイルはスキップ
                continue

        if spinner:
            spinner.stop(True)

        if self.verbose:
            self.logger.info("✅ 命名規則チェック")

        # 問題が見つかった場合は警告として追加
        if naming_issues:
            self.issues.append("命名規則の問題が検出されました:")
            for issue in naming_issues[:15]:  # 最大15件表示
                self.issues.append(f"  {issue}")

            if len(naming_issues) > 15:
                self.issues.append(f"  ... 他{len(naming_issues) - 15}件")

        return True  # 警告レベルなので常にTrueを返す
