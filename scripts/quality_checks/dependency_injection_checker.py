#!/usr/bin/env python3
"""
依存性注入チェッカー - 副作用はinfrastructure外で直接使用禁止
"""

import ast
import glob
from typing import List

from infrastructure.file_handler import FileHandler
from infrastructure.logger import Logger


class DependencyInjectionChecker:
    def __init__(self, file_handler: FileHandler, logger: Logger, issues: List[str], verbose: bool = False):
        self.file_handler = file_handler
        self.logger = logger
        self.issues = issues
        self.verbose = verbose

    def check_dependency_injection(self) -> bool:
        """依存性注入チェック - 副作用はinfrastructure外で直接使用禁止"""
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
            spinner = ProgressSpinner("依存性注入チェック", self.logger)
            spinner.start()

        injection_issues = []

        # 副作用パターン（直接使用禁止）
        side_effect_patterns = {
            'subprocess': ['run', 'Popen', 'call', 'check_call', 'check_output'],
            'shutil': ['copy', 'copy2', 'copytree', 'move', 'rmtree'],
            'sqlite3': ['connect'],
            'sys': ['stdout.write', 'stderr.write'],
            'os': ['system', 'popen', 'utime', 'chmod', 'chown'],
            'pathlib.Path': ['write_text', 'write_bytes', 'mkdir', 'rmdir', 'unlink'],
            'docker': ['from_env', 'DockerClient'],
            'json': ['dump', 'dumps'],  # ファイル書き込み系のみ
            'yaml': ['dump', 'safe_dump'],
            'toml': ['dump']
        }

        # 許可されたディレクトリ（CLAUDE.mdに従い、infrastructure層全体を許可）
        allowed_dirs = [
            'src/infrastructure/',
            'tests/infrastructure/'
        ]

        for file_path in glob.glob('src/**/*.py', recursive=True):
            # 許可されたディレクトリは除外
            if any(file_path.startswith(allowed_dir) for allowed_dir in allowed_dirs):
                continue

            try:
                content = self.file_handler.read_text(file_path, encoding='utf-8')
                tree = ast.parse(content, filename=file_path)

                relative_path = file_path.replace('src/', '')

                # インポート文と使用箇所をチェック
                for node in ast.walk(tree):
                    # from subprocess import run のようなケース
                    if isinstance(node, ast.ImportFrom) and node.module:
                        module = node.module
                        if module in side_effect_patterns:
                            for alias in node.names or []:
                                if alias.name in side_effect_patterns[module]:
                                    injection_issues.append(
                                        f"{relative_path}:{node.lineno} from {module} import {alias.name} (副作用の直接インポート)"
                                    )

                    # import subprocess のようなケース
                    elif isinstance(node, ast.Import):
                        for alias in node.names:
                            if alias.name in side_effect_patterns:
                                injection_issues.append(
                                    f"{relative_path}:{node.lineno} import {alias.name} (副作用モジュールの直接インポート)"
                                )

                    # subprocess.run() のような使用
                    elif isinstance(node, ast.Call):
                        if isinstance(node.func, ast.Attribute):
                            # モジュール.メソッド の形式
                            if isinstance(node.func.value, ast.Name):
                                module_name = node.func.value.id
                                method_name = node.func.attr
                                if module_name in side_effect_patterns and method_name in side_effect_patterns[module_name]:
                                    injection_issues.append(
                                        f"{relative_path}:{node.lineno} {module_name}.{method_name}() (副作用の直接使用)"
                                    )
                            # sys.stdout.write のような多段階アクセス
                            elif isinstance(node.func.value, ast.Attribute):
                                if isinstance(node.func.value.value, ast.Name):
                                    base_module = node.func.value.value.id
                                    attr_chain = f"{node.func.value.attr}.{node.func.attr}"
                                    if base_module in side_effect_patterns and attr_chain in side_effect_patterns[base_module]:
                                        injection_issues.append(
                                            f"{relative_path}:{node.lineno} {base_module}.{attr_chain}() (副作用の直接使用)"
                                        )

                        # 直接関数呼び出し（from import で取り込んだ場合）
                        elif isinstance(node.func, ast.Name):
                            func_name = node.func.id
                            # 各モジュールの関数名をチェック
                            for _module, functions in side_effect_patterns.items():
                                if func_name in functions:
                                    injection_issues.append(
                                        f"{relative_path}:{node.lineno} {func_name}() (副作用関数の直接使用)"
                                    )

            except SyntaxError:
                # 構文エラーのファイルはスキップ
                continue

        success = len(injection_issues) == 0

        if spinner:
            spinner.stop(success)
        elif self.verbose:
            self.logger.info(f"{'✅' if success else '❌'} 依存性注入チェック")

        if injection_issues:
            self.issues.append("副作用の直接使用が検出されました（infrastructure層での注入が必要）:")
            for issue in injection_issues[:25]:  # 最大25件表示
                self.issues.append(f"  {issue}")

            if len(injection_issues) > 25:
                self.issues.append(f"  ... 他{len(injection_issues) - 25}件")

            return False

        return success
