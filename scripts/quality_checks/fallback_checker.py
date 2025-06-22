#!/usr/bin/env python3
"""
フォールバック処理チェッカー - エラー隠蔽防止
"""

import ast
import glob
import re
from typing import List

from infrastructure.file_handler import FileHandler
from infrastructure.logger import Logger


class FallbackChecker:
    def __init__(self, file_handler: FileHandler, logger: Logger, issues: List[str], verbose: bool = False):
        self.file_handler = file_handler
        self.logger = logger
        self.issues = issues
        self.verbose = verbose

    def check_fallback_patterns(self) -> bool:
        """フォールバック処理の検出（CLAUDE.mdルール違反 - エラー隠蔽防止）"""
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
            spinner = ProgressSpinner("フォールバック処理チェック", self.logger)
            spinner.start()

        fallback_issues = []

        for file_path in glob.glob('src/**/*.py', recursive=True):
            # Infrastructure層は許可されているためスキップ
            if file_path.startswith('src/infrastructure/'):
                continue

            try:
                content = self.file_handler.read_text(file_path, encoding='utf-8')
                tree = ast.parse(content, filename=file_path)
                relative_path = file_path.replace('src/', '')
                content_lines = content.splitlines()

                for node in ast.walk(tree):
                    # 1. try-except内での代入・return（必要なエラーハンドリングを除外）
                    if isinstance(node, ast.Try):
                        for handler in node.handlers:
                            for stmt in handler.body:
                                if isinstance(stmt, (ast.Assign, ast.Return)):
                                    line = content_lines[stmt.lineno - 1].strip() if stmt.lineno <= len(content_lines) else ""
                                    # 必要なエラーハンドリングパターンを除外
                                    if not self._is_legitimate_error_handling(line):
                                        fallback_issues.append(f"{relative_path}:{stmt.lineno} try-except内でのフォールバック: {line}")

                    # 2. or演算子での値指定（論理演算は除外）
                    elif isinstance(node, ast.BoolOp) and isinstance(node.op, ast.Or):
                        if len(node.values) >= 2:
                            line = content_lines[node.lineno - 1].strip() if node.lineno <= len(content_lines) else ""
                            if re.search(r'or\s+["\'\[\{0-9]', line) and not self._is_logical_or_check(line):  # or の後にリテラル値で論理的なチェック以外
                                fallback_issues.append(f"{relative_path}:{node.lineno} or演算子でのフォールバック: {line}")

                    # 3. 条件式での値指定（適切な条件分岐は除外）
                    elif isinstance(node, ast.IfExp):
                        line = content_lines[node.lineno - 1].strip() if node.lineno <= len(content_lines) else ""
                        if re.search(r'else\s+["\'\[\{0-9]', line) and not self._is_legitimate_conditional(line):  # else の後にリテラル値で適切な条件分岐以外
                            fallback_issues.append(f"{relative_path}:{node.lineno} 条件式でのフォールバック: {line}")

            except (SyntaxError, UnicodeDecodeError, OSError, FileNotFoundError):
                continue

        success = len(fallback_issues) == 0

        if spinner:
            spinner.stop(success)
        elif self.verbose:
            self.logger.info(f"{'✅' if success else '❌'} try-except処理チェック")

        if fallback_issues:
            self.issues.append("try-except処理が検出されました（CLAUDE.mdルール違反）:")
            for issue in fallback_issues[:20]:
                self.issues.append(f"  {issue}")

            if len(fallback_issues) > 20:
                self.issues.append(f"  ... 他{len(fallback_issues) - 20}件")

        return success

    def _is_legitimate_error_handling(self, line: str) -> bool:
        """正当なエラーハンドリングパターンを判定"""
        legitimate_patterns = [
            'last_exception', 'error_code', 'return_code', 'status_code',
            'logger', 'log', 'should_retry', 'attempt', 'retry',
            'raise', 'exception', 'error_msg', 'error_message',
            '_handle_', 'handle_', 'end_time', 'time.', 'perf_counter',
            'operationresult', 'result', 'error_step', 'step(', 'format_'
        ]
        return any(pattern in line.lower() for pattern in legitimate_patterns)

    def _is_logical_or_check(self, line: str) -> bool:
        """論理的なorチェックを判定"""
        logical_patterns = [
            'in ', ' and ', ' or ', 'is ', 'not ', '==', '!=',
            'registry', 'check', 'validate', 'contains'
        ]
        return any(pattern in line.lower() for pattern in logical_patterns)

    def _is_legitimate_conditional(self, line: str) -> bool:
        """適切な条件分岐パターンを判定"""
        conditional_patterns = [
            'if ', 'else', 'version', 'row', 'value', 'result',
            'config', 'default', 'none'
        ]
        return any(pattern in line.lower() for pattern in conditional_patterns)
