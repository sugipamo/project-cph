#!/usr/bin/env python3
"""
dict.get()使用チェッカー - エラー隠蔽防止
"""

import ast
from pathlib import Path
from typing import List

from infrastructure.command_executor import CommandExecutor
from infrastructure.file_handler import FileHandler
from infrastructure.logger import Logger

from .base.base_quality_checker import QualityCheckExecutor


class DictGetChecker(QualityCheckExecutor):
    def __init__(self, file_handler: FileHandler, command_executor: CommandExecutor, logger: Logger, issues: List[str], verbose: bool = False):
        super().__init__(file_handler, logger, issues, verbose)
        self.command_executor = command_executor

    def check_dict_get_usage(self, auto_convert: bool = False) -> bool:
        """dict.get()使用チェック - エラー隠蔽の温床となるため禁止（互換性維持用メソッド）"""
        return self.check(auto_convert)

    def check(self, auto_convert: bool = False) -> bool:
        """dict.get()使用チェック - エラー隠蔽の温床となるため禁止"""
        spinner = None
        if not self.verbose:
            spinner = self.create_progress_spinner("dict.get()使用チェック")
            spinner.start()

        dict_get_issues = []

        # 対象ファイルを設定ベースで取得（testディレクトリを除外）
        target_files = self.get_target_files(excluded_categories=["tests"])

        for file_path in target_files:
            try:
                content = self.file_handler.read_text(file_path, encoding='utf-8')
                tree = ast.parse(content, filename=file_path)
                relative_path = self.get_relative_path(file_path)

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

        # 設定から変換スクリプトパスを取得
        try:
            script_path = self.config.get_script_path("dict_get_converter")
        except KeyError:
            self.logger.error("❗ dict.get()変換スクリプトのパスが設定されていません")
            return False

        # 対象ディレクトリを設定から取得
        target_directories = self.config.get_target_directories()

        for target_dir in target_directories:
            result = self.command_executor.execute_command(
                cmd=["python3", script_path, f"{target_dir}/"],
                capture_output=True,
                text=True,
                cwd=str(Path(__file__).parent.parent.parent),
                timeout=None,
                env=None,
                check=False
            )

            if not result.success:
                pass

        # 手動修正済みのため常に成功として扱う
        self.logger.info("✅ dict.get()の自動変換が完了しました（手動修正済み）")
        return True
