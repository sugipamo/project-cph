#!/usr/bin/env python3
"""
循環インポート検出スクリプト
"""
import ast
import sys
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Set


class CircularImportChecker:
    def __init__(self):
        self.imports: Dict[str, Set[str]] = defaultdict(set)
        self.modules: Set[str] = set()

    def analyze_file(self, file_path: Path) -> None:
        """ファイルの依存関係を解析"""
        try:
            with open(file_path, encoding='utf-8') as f:
                tree = ast.parse(f.read(), filename=str(file_path))

            # ファイルパスをモジュール名に変換
            module_name = self._path_to_module(file_path)
            self.modules.add(module_name)

            # インポート文を解析
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        if alias.name.startswith('src.'):
                            self.imports[module_name].add(alias.name)

                elif isinstance(node, ast.ImportFrom) and node.module and node.module.startswith('src.'):
                        self.imports[module_name].add(node.module)

        except Exception as e:
            print(f"Warning: Failed to analyze {file_path}: {e}")

    def _path_to_module(self, file_path: Path) -> str:
        """ファイルパスをモジュール名に変換"""
        try:
            relative_path = file_path.relative_to(Path.cwd())
        except ValueError:
            # 絶対パスの場合の処理
            relative_path = file_path

        if relative_path.parts[0] == 'src':
            parts = relative_path.parts[1:]
        else:
            parts = relative_path.parts

        module_parts = []
        for part in parts:
            if part.endswith('.py'):
                if part != '__init__.py':
                    module_parts.append(part[:-3])
            else:
                module_parts.append(part)

        return 'src.' + '.'.join(module_parts) if module_parts else 'src'

    def find_cycles(self) -> List[List[str]]:
        """循環依存を検出"""
        cycles = []
        visited = set()
        rec_stack = set()

        def dfs(module: str, path: List[str]) -> bool:
            if module in rec_stack:
                # 循環を発見
                cycle_start = path.index(module)
                cycle = path[cycle_start:] + [module]
                cycles.append(cycle)
                return True

            if module in visited:
                return False

            visited.add(module)
            rec_stack.add(module)
            path.append(module)

            for imported_module in self.imports[module]):
                if imported_module in self.modules:
                    dfs(imported_module, path.copy())

            rec_stack.remove(module)
            return False

        for module in self.modules:
            if module not in visited:
                dfs(module, [])

        return cycles


def main():
    """メイン処理"""
    if len(sys.argv) < 2:
        print("Usage: python check_circular_imports.py <directory>")
        sys.exit(1)

    search_dir = Path(sys.argv[1])
    checker = CircularImportChecker()

    # Python ファイルを解析
    for py_file in search_dir.rglob("*.py"):
        if '__pycache__' not in str(py_file):
            checker.analyze_file(py_file)

    # 循環依存を検出
    cycles = checker.find_cycles()

    if cycles:
        print("🚨 循環インポートが見つかりました:")
        for i, cycle in enumerate(cycles[:10], 1):
            print(f"\n{i}. 循環依存:")
            for j, module in enumerate(cycle):
                if j == len(cycle) - 1:
                    print(f"   {module} -> {cycle[0]}")
                else:
                    print(f"   {module} ->")

        if len(cycles) > 10:
            print(f"\n... and {len(cycles) - 10} more cycles")

        print("\n💡 解決方法:")
        print("  1. 共通機能を別モジュールに抽出")
        print("  2. インポートをローカル化（関数内import）")
        print("  3. 依存関係を一方向にリファクタリング")

        sys.exit(1)
    else:
        print("✅ 循環インポートは見つかりませんでした")


if __name__ == "__main__":
    main()
