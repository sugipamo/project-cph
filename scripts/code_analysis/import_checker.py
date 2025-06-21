#!/usr/bin/env python3
"""
インポート解決チェッカー
"""

import ast
import glob
from pathlib import Path
from typing import List

from infrastructure.file_handler import FileHandler
from infrastructure.logger import Logger


class ImportChecker:
    def __init__(self, file_handler: FileHandler, logger: Logger, issues: List[str], verbose: bool = False):
        self.file_handler = file_handler
        self.logger = logger
        self.issues = issues
        self.verbose = verbose

    def check_import_resolution(self) -> bool:
        """インポート解決チェック - ファイル移動・削除で破綻したインポートを検出"""
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
            spinner = ProgressSpinner("インポート解決チェック", self.logger)
            spinner.start()

        import_issues = []

        for file_path in glob.glob('src/**/*.py', recursive=True):
            try:
                content = self.file_handler.read_text(file_path, encoding='utf-8')
                tree = ast.parse(content, filename=file_path)

                # import文を解析
                for node in ast.walk(tree):
                    if isinstance(node, ast.ImportFrom) and node.module:
                        module = node.module
                        if module.startswith('src.'):
                            # モジュールパスの存在確認
                            # src.context.user_input_parser -> src/context/user_input_parser.py
                            module_path = module.replace('.', '/') + '.py'
                            # または __init__.py での初期化
                            init_path = module.replace('.', '/') + '/__init__.py'

                            if not (Path(module_path).exists() or Path(init_path).exists()):
                                relative_file = file_path.replace('src/', '') if file_path.startswith('src/') else file_path
                                import_issues.append(f"{relative_file}: import {module} (モジュールが見つかりません)")

                    elif isinstance(node, ast.Import):
                        for alias in node.names:
                            module = alias.name
                            if module.startswith('src.'):
                                module_path = module.replace('.', '/') + '.py'
                                init_path = module.replace('.', '/') + '/__init__.py'

                                if not (Path(module_path).exists() or Path(init_path).exists()):
                                    relative_file = file_path.replace('src/', '') if file_path.startswith('src/') else file_path
                                    import_issues.append(f"{relative_file}: import {module} (モジュールが見つかりません)")

            except (SyntaxError, UnicodeDecodeError, OSError, FileNotFoundError):
                # 構文エラーやファイル読み込みエラーは無視
                continue

        success = len(import_issues) == 0

        if spinner:
            spinner.stop(success)
        elif self.verbose:
            self.logger.info(f"{'✅' if success else '❌'} インポート解決チェック")

        if import_issues:
            self.issues.append("インポート解決エラーが検出されました:")
            for issue in import_issues[:15]:  # 最大15件表示
                self.issues.append(f"  {issue}")

            if len(import_issues) > 15:
                self.issues.append(f"  ... 他{len(import_issues) - 15}件")

        return success
