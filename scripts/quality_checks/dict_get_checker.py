#!/usr/bin/env python3
"""
dict.get()使用チェッカー - エラー隠蔽防止
"""

import ast
import glob
from pathlib import Path
from typing import List

from infrastructure.command_executor import CommandExecutor
from infrastructure.file_handler import FileHandler
from infrastructure.logger import Logger


class DictGetChecker:
    def __init__(self, file_handler: FileHandler, command_executor: CommandExecutor, logger: Logger, issues: List[str], verbose: bool = False):
        self.file_handler = file_handler
        self.command_executor = command_executor
        self.logger = logger
        self.issues = issues
        self.verbose = verbose

    def check_dict_get_usage(self, auto_convert: bool = False) -> bool:
        """dict.get()使用チェック - エラー隠蔽の温床となるため禁止"""
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
            spinner = ProgressSpinner("dict.get()使用チェック", self.logger)
            spinner.start()

        dict_get_issues = []

        for file_path in glob.glob('src/**/*.py', recursive=True):
            try:
                content = self.file_handler.read_text(file_path, encoding='utf-8')
                tree = ast.parse(content, filename=file_path)
                relative_path = file_path.replace('src/', '')

                # AST解析によるより正確な.get()メソッド検出
                for node in ast.walk(tree):
                    if (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and
                        node.func.attr == 'get'):
                        # .get() メソッド呼び出しを検出
                        # 正当な使用パターンを除外
                        if self._is_legitimate_get_usage(node, content):
                            continue

                        # 変数名やオブジェクト名から、辞書の可能性を判定
                        if self._is_likely_dict_get(node):
                            context_line = self._get_source_line(content, node.lineno)
                            dict_get_issues.append(f"{relative_path}:{node.lineno} {context_line.strip()}")

            except (SyntaxError, UnicodeDecodeError, OSError, FileNotFoundError):
                # 構文エラーやファイル読み込みエラーは無視
                continue

        success = len(dict_get_issues) == 0

        if spinner:
            spinner.stop(success)
        elif self.verbose:
            self.logger.info(f"{'✅' if success else '❌'} dict.get()使用チェック")

        if dict_get_issues:
            # 自動変換を実行（フォールバック処理は禁止のため、変換失敗時は直接エラー表示）
            if not auto_convert and self._auto_convert_dict_get():
                # 変換成功時のみ再チェック（1回のみ）
                return self.check_dict_get_usage(auto_convert=True)

            # エラー表示
            self.issues.append("dict.get()の使用が検出されました（エラー隠蔽防止・フォールバック対応禁止のため使用禁止）:")
            for issue in dict_get_issues[:20]:  # 最大20件表示
                self.issues.append(f"  {issue}")

            if len(dict_get_issues) > 20:
                self.issues.append(f"  ... 他{len(dict_get_issues) - 20}件")

            return False

        return success

    def _is_legitimate_get_usage(self, node: ast.Call, content: str) -> bool:
        """正当な.get()使用パターンを判定"""
        # HTTP/APIクライアントのGETメソッド
        if isinstance(node.func.value, ast.Name):
            var_name = node.func.value.id.lower()
            if any(keyword in var_name for keyword in ['client', 'session', 'request', 'http', 'api']):
                return True

        # 設定取得メソッド（get_config, get_setting等）
        context_line = self._get_source_line(content, node.lineno).lower()
        if any(pattern in context_line for pattern in ['get_config', 'get_setting', 'getattr', 'get_user', 'get_data']):
            return True

        # クラスのgetterメソッド
        return bool(hasattr(node.func.value, 'attr') and node.func.value.attr.startswith('get_'))

    def _is_likely_dict_get(self, node: ast.Call) -> bool:
        """辞書のget()メソッドである可能性を判定"""
        if isinstance(node.func.value, ast.Name):
            var_name = node.func.value.id.lower()
            # 辞書を示唆する変数名
            dict_indicators = ['dict', 'config', 'data', 'params', 'options', 'settings', 'mapping', 'cache']
            if any(indicator in var_name for indicator in dict_indicators):
                return True

        # 辞書リテラルから直接呼び出し: {}.get()
        if isinstance(node.func.value, ast.Dict):
            return True

        # インデックスアクセスの結果: data[key].get()
        if isinstance(node.func.value, ast.Subscript):
            return True

        # デフォルト値が指定されている場合（dict.get()の典型的な使用法）
        return len(node.args) > 1

    def _get_source_line(self, content: str, line_num: int) -> str:
        """指定行のソースコードを取得"""
        lines = content.splitlines()
        if 1 <= line_num <= len(lines):
            return lines[line_num - 1]
        return ""

    def _auto_convert_dict_get(self) -> bool:
        """dict.get()を自動変換"""
        self.logger.info("🔧 dict.get()の自動変換を実行中...")

        result = self.command_executor.run([
            "python3", "scripts/quality/convert_dict_get.py", "src/"
        ], capture_output=True, text=True, cwd=str(Path(__file__).parent.parent.parent))

        if result.success:
            self.logger.info("✅ dict.get()の自動変換が完了しました")
            if result.stdout.strip():
                self.logger.info("変換結果:")
                for line in result.stdout.strip().split('\n'):
                    if line.strip():
                        self.logger.info(f"   {line}")
            return True
        self.logger.error("❌ dict.get()の自動変換中にエラーが発生しました")
        if result.stderr.strip():
            self.logger.error(f"エラー: {result.stderr}")
        return False
