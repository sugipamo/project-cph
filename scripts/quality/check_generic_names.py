#!/usr/bin/env python3
"""
汎用的すぎる名前を検出するカスタムチェッカー
"""
import ast
import re
import sys
from pathlib import Path
from typing import List, Set

sys.path.insert(0, str(Path(__file__).parent.parent))

from infrastructure.file_handler import FileHandler
from infrastructure.logger import Logger, create_logger
from infrastructure.system_operations import SystemOperations

# 汎用的すぎる名前のパターン（実用的なレベルに緩和）
GENERIC_PATTERNS = {
    'variables': [
        # 本当に問題のある汎用名のみ
        r'^var$', r'^val$', r'^tmp$', r'^temp$', r'^thing$', r'^stuff$',
        r'^obj$', r'^item$', r'^elem$', r'^pure$',
        # pureが含まれる変数名（末尾のpureを検出）
        r'.*_pure$',
        # 単独の型名は避ける
        r'^list$', r'^dict$', r'^string$', r'^number$',
    ],
    'functions': [
        # 意味が全く不明な関数名のみ
        r'^do$', r'^func$', r'^method$', r'^action$', r'^pure$',
        # pureが含まれる関数名（末尾のpureを検出）
        r'.*_pure$',
        # 単独の動詞は文脈によって許可
        # r'^process$', r'^handle$', r'^run$' などは削除
    ],
    'classes': [
        # 意味のないクラス名のみ
        r'^Object$', r'^Thing$', r'^Item$', r'^Stuff$', r'^Pure$',
        # Manager, Handler, Processor などは一般的なパターンなので許可
    ]
}

# 許可される名前（例外） - 大幅に拡充
ALLOWED_NAMES = {
    'variables': {
        # ループ変数
        'i', 'j', 'k', 'n', 'm',
        # 座標・数学
        'x', 'y', 'z', 'w', 'h',
        # 標準的な短縮形
        'f',  # ファイルオブジェクト
        'e',  # 例外
        '_',  # 未使用変数
        'p',  # パス（文脈で明確）
        # 引数
        'args', 'kwargs',
        # 一般的で文脈が明確な名前
        'path', 'file', 'name', 'id', 'key', 'value',
        'data', 'info', 'config', 'params', 'content',
        'result', 'output', 'input', 'text', 'count',
        'node', 'root', 'parent', 'child',
    },
    'functions': {
        # エントリーポイント
        'main',
        # テストメソッド
        'setUp', 'tearDown',
        # 特殊メソッド
        '__init__', '__str__', '__repr__', '__call__',
        '__enter__', '__exit__', '__iter__', '__next__',
        # 一般的な動詞（文脈で意味が明確）
        'run', 'get', 'set', 'put', 'post', 'delete',
        'create', 'update', 'read', 'write', 'open', 'close',
        'start', 'stop', 'build', 'parse', 'load', 'save',
        'check', 'validate', 'process', 'handle', 'execute',
        'convert', 'transform', 'format', 'render',
    },
    'classes': {
        # メタクラス
        'Meta',
        # 一般的なパターン（意味が明確）
        'Manager', 'Handler', 'Processor', 'Helper',
        'Service', 'Controller', 'Factory', 'Builder',
        'Parser', 'Formatter', 'Validator', 'Converter',
    }
}

class VagueNameDetector(ast.NodeVisitor):
    def __init__(self):
        self.errors: List[str] = []

    def _check_name(self, name: str, patterns: List[str], allowed: Set[str],
                   node_type: str, lineno: int) -> None:
        """名前をチェックして汎用的すぎる場合はエラーを記録"""
        if name in allowed:
            return

        for pattern in patterns:
            if re.match(pattern, name):
                self.errors.append(
                    f"Line {lineno}: Generic {node_type} name '{name}' - "
                    f"use more descriptive name"
                )
                break

    def visit_FunctionDef(self, node):
        """関数名をチェック"""
        self._check_name(
            node.name,
            GENERIC_PATTERNS['functions'],
            ALLOWED_NAMES['functions'],
            'function',
            node.lineno
        )

        # 引数名もチェック
        for arg in node.args.args:
            self._check_name(
                arg.arg,
                GENERIC_PATTERNS['variables'],
                ALLOWED_NAMES['variables'],
                'parameter',
                node.lineno
            )

        self.generic_visit(node)

    def visit_ClassDef(self, node):
        """クラス名をチェック"""
        self._check_name(
            node.name,
            GENERIC_PATTERNS['classes'],
            ALLOWED_NAMES['classes'],
            'class',
            node.lineno
        )
        self.generic_visit(node)

    def visit_Assign(self, node):
        """変数代入をチェック"""
        for target in node.targets:
            if isinstance(target, ast.Name):
                self._check_name(
                    target.id,
                    GENERIC_PATTERNS['variables'],
                    ALLOWED_NAMES['variables'],
                    'variable',
                    node.lineno
                )
        self.generic_visit(node)

def check_file(file_path: Path, file_handler: FileHandler) -> List[str]:
    """ファイル内の汎用名をチェック"""
    try:
        content = file_handler.read_text(file_path, encoding='utf-8')

        tree = ast.parse(content, filename=str(file_path))
        checker = VagueNameDetector()
        checker.visit(tree)

        # ファイル名を含めてエラーメッセージを返す
        return [f"{file_path}:{error}" for error in checker.errors]

    except Exception as e:
        raise RuntimeError(f"ファイル解析エラー {file_path}: {e}") from e

def main(logger: Logger, system_ops: SystemOperations, file_handler: FileHandler):
    """メイン処理"""

    argv = system_ops.get_argv()
    if len(argv) < 2:
        logger.error("Usage: python check_generic_names.py <directory>")
        system_ops.exit(1)

    search_dir = Path(argv[1])
    if not file_handler.exists(search_dir):
        logger.error(f"Directory not found: {search_dir}")
        system_ops.exit(1)

    all_errors = []

    # Python ファイルを再帰的に検索
    python_files = file_handler.glob("**/*.py", search_dir)
    for py_file in python_files:
        # __pycache__ や .git は除外
        if '__pycache__' in str(py_file) or '.git' in str(py_file):
            continue

        errors = check_file(py_file, file_handler)
        all_errors.extend(errors)

    if all_errors:
        logger.error("🚨 汎用的すぎる名前が見つかりました:")
        for error in all_errors[:20]:  # 最初の20個のみ表示
            logger.error(f"  {error}")

        if len(all_errors) > 20:
            logger.error(f"  ... and {len(all_errors) - 20} more")

        logger.info("\n💡 改善例:")
        logger.info("  ❌ calculate_result_pure() -> ✅ calculate_result(), compute_total()")
        logger.info("  ❌ build_command_pure() -> ✅ build_docker_command(), create_command()")
        logger.info("  ❌ pure, var, tmp -> ✅ calculation_result, user_data, temp_file")
        logger.info("  ❌ thing, stuff -> ✅ payment_info, config_data")

        system_ops.exit(1)
    else:
        logger.info("✅ 汎用名チェック完了")

if __name__ == "__main__":
    # 互換性維持: 既存のテストで動作するよう直接インポートを保持
    import os
    import sys

    from infrastructure.file_handler import create_file_handler
    from infrastructure.system_operations_impl import SystemOperationsImpl

    # 依存性注入用のプロバイダーを作成
    class OSProvider:
        def getcwd(self): return os.getcwd()
        def chdir(self, path): os.chdir(path)
        def path_exists(self, path): return os.path.exists(path)
        def isfile(self, path): return os.path.isfile(path)
        def isdir(self, path): return os.path.isdir(path)
        def makedirs(self, path, exist_ok): os.makedirs(path, exist_ok=exist_ok)
        def remove(self, path): os.remove(path)
        def rmdir(self, path): os.rmdir(path)
        def listdir(self, path): return os.listdir(path)
        def get_env(self, key): return os.environ.get(key)
        def set_env(self, key, value): os.environ[key] = value

    class SysProvider:
        def exit(self, code): sys.exit(code)
        def get_argv(self): return sys.argv
        def print_stdout(self, message): print(message)

    system_ops = SystemOperationsImpl(OSProvider(), SysProvider())
    file_handler = create_file_handler(mock=False, file_operations=None)
    logger = create_logger(verbose=False, silent=False, system_operations=system_ops)
    main(logger, system_ops, file_handler)
