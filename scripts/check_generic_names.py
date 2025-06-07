#!/usr/bin/env python3
"""
汎用的すぎる名前を検出するカスタムチェッカー
"""
import ast
import re
import sys
from pathlib import Path
from typing import List, Set

# 汎用的すぎる名前のパターン
GENERIC_PATTERNS = {
    'variables': [
        r'^data$', r'^info$', r'^obj$', r'^item$', r'^value$',
        r'^result$', r'^output$', r'^input$', r'^content$',
        r'^text$', r'^string$', r'^number$', r'^count$',
        r'^list$', r'^dict$', r'^config$', r'^params$',
        r'^var$', r'^val$', r'^elem$', r'^node$',
        r'^file$', r'^path$', r'^name$', r'^id$',
    ],
    'functions': [
        r'^process$', r'^handle$', r'^execute$', r'^run$',
        r'^do$', r'^get$', r'^set$', r'^create$', r'^make$',
        r'^build$', r'^parse$', r'^load$', r'^save$',
        r'^update$', r'^check$', r'^validate$',
        r'^convert$', r'^transform$',
    ],
    'classes': [
        r'^Data$', r'^Info$', r'^Object$', r'^Item$',
        r'^Manager$', r'^Handler$', r'^Processor$',
        r'^Helper$', r'^Utility$', r'^Utils$',
    ]
}

# 許可される名前（例外）
ALLOWED_NAMES = {
    'variables': {
        'i', 'j', 'k',  # ループカウンター
        'x', 'y', 'z',  # 座標
        'f',  # ファイルオブジェクト
        'e',  # 例外
        '_',  # 未使用変数
        'args', 'kwargs',  # 標準的な引数名
    },
    'functions': {
        'main',  # エントリーポイント
        'setUp', 'tearDown',  # テストメソッド
        '__init__', '__str__', '__repr__',  # 特殊メソッド
    },
    'classes': {
        'Meta',  # Django等のメタクラス
    }
}

class GenericNameChecker(ast.NodeVisitor):
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

def check_file(file_path: Path) -> List[str]:
    """ファイル内の汎用名をチェック"""
    try:
        with open(file_path, encoding='utf-8') as f:
            content = f.read()

        tree = ast.parse(content, filename=str(file_path))
        checker = GenericNameChecker()
        checker.visit(tree)

        # ファイル名を含めてエラーメッセージを返す
        return [f"{file_path}:{error}" for error in checker.errors]

    except Exception as e:
        return [f"{file_path}: Error parsing file - {e}"]

def main():
    """メイン処理"""
    if len(sys.argv) < 2:
        print("Usage: python check_generic_names.py <directory>")
        sys.exit(1)

    search_dir = Path(sys.argv[1])
    if not search_dir.exists():
        print(f"Directory not found: {search_dir}")
        sys.exit(1)

    all_errors = []

    # Python ファイルを再帰的に検索
    for py_file in search_dir.rglob("*.py"):
        # __pycache__ や .git は除外
        if '__pycache__' in str(py_file) or '.git' in str(py_file):
            continue

        errors = check_file(py_file)
        all_errors.extend(errors)

    if all_errors:
        print("🚨 汎用的すぎる名前が見つかりました:")
        for error in all_errors[:20]:  # 最初の20個のみ表示
            print(f"  {error}")

        if len(all_errors) > 20:
            print(f"  ... and {len(all_errors) - 20} more")

        print("\n💡 改善例:")
        print("  ❌ data -> ✅ user_data, config_data")
        print("  ❌ process() -> ✅ process_payment(), process_order()")
        print("  ❌ result -> ✅ calculation_result, api_response")

        sys.exit(1)
    else:
        print("✅ 汎用名チェック完了")

if __name__ == "__main__":
    main()
