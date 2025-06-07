#!/usr/bin/env python3
"""
未使用ファイルの検出スクリプト
"""
import os
import ast
import sys
from pathlib import Path
from collections import defaultdict
from typing import Set, Dict, List, Tuple

class ImportAnalyzer(ast.NodeVisitor):
    """ASTを解析してインポートを抽出"""
    def __init__(self):
        self.imports = set()
        self.from_imports = defaultdict(set)
    
    def visit_Import(self, node):
        for alias in node.names:
            self.imports.add(alias.name)
    
    def visit_ImportFrom(self, node):
        if node.module:
            for alias in node.names:
                self.from_imports[node.module].add(alias.name)
        self.generic_visit(node)

def get_python_files(root_dir: str, exclude_dirs: Set[str] = None) -> List[Path]:
    """Pythonファイルを再帰的に取得"""
    if exclude_dirs is None:
        exclude_dirs = {'__pycache__', '.git', 'venv', 'env', '.pytest_cache', 'tests'}
    
    python_files = []
    for root, dirs, files in os.walk(root_dir):
        dirs[:] = [d for d in dirs if d not in exclude_dirs]
        for file in files:
            if file.endswith('.py') and not file.startswith('test_'):
                python_files.append(Path(root) / file)
    return python_files

def analyze_imports(file_path: Path) -> Tuple[Set[str], Dict[str, Set[str]]]:
    """ファイルのインポートを解析"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            tree = ast.parse(f.read())
        
        analyzer = ImportAnalyzer()
        analyzer.visit(tree)
        return analyzer.imports, analyzer.from_imports
    except Exception as e:
        print(f"Error analyzing {file_path}: {e}")
        return set(), {}

def get_module_path(file_path: Path, root_dir: Path) -> str:
    """ファイルパスからモジュールパスを生成"""
    relative_path = file_path.relative_to(root_dir)
    module_path = str(relative_path.with_suffix('')).replace(os.sep, '.')
    return module_path

def find_unused_files(root_dir: str) -> Tuple[List[Path], Dict[Path, Set[Path]]]:
    """未使用のファイルを検出"""
    root_path = Path(root_dir)
    src_path = root_path / 'src'
    
    # すべてのPythonファイルを取得
    all_files = get_python_files(src_path)
    
    # ファイルごとのインポート関係を構築
    import_graph = defaultdict(set)  # file -> imported files
    module_to_file = {}  # module path -> file path
    
    # モジュールパスとファイルパスのマッピングを作成
    for file_path in all_files:
        module_path = get_module_path(file_path, root_path)
        module_to_file[module_path] = file_path
    
    # インポート関係を解析
    for file_path in all_files:
        imports, from_imports = analyze_imports(file_path)
        
        # インポートされているファイルを記録
        for imp in imports:
            if imp.startswith('src.'):
                imported_module = imp
                # サブモジュールも含めて検索
                for module, file in module_to_file.items():
                    if module == imported_module or module.startswith(imported_module + '.'):
                        import_graph[file_path].add(file)
        
        for module, names in from_imports.items():
            if module and module.startswith('src.'):
                # モジュールのファイルを検索
                for mod_path, file in module_to_file.items():
                    if mod_path == module or mod_path.startswith(module + '.'):
                        import_graph[file_path].add(file)
    
    # エントリーポイントから到達可能なファイルを探索
    entry_points = [
        src_path / 'main.py',
        src_path / 'cli' / '__init__.py',
    ]
    
    # テストファイルもエントリーポイントとして追加
    test_files = get_python_files(root_path / 'tests', exclude_dirs={'__pycache__'})
    
    reachable = set()
    to_visit = set()
    
    # エントリーポイントを追加
    for entry in entry_points:
        if entry.exists():
            to_visit.add(entry)
    
    # テストからインポートされているファイルも到達可能とする
    for test_file in test_files:
        imports, from_imports = analyze_imports(test_file)
        for imp in imports:
            if imp.startswith('src.'):
                for module, file in module_to_file.items():
                    if module == imp or module.startswith(imp + '.'):
                        to_visit.add(file)
        
        for module, names in from_imports.items():
            if module and module.startswith('src.'):
                for mod_path, file in module_to_file.items():
                    if mod_path == module or mod_path.startswith(module + '.'):
                        to_visit.add(file)
    
    # BFSで到達可能なファイルを探索
    while to_visit:
        current = to_visit.pop()
        if current not in reachable and current in all_files:
            reachable.add(current)
            to_visit.update(import_graph[current])
    
    # __init__.pyは特別扱い（パッケージマーカーとして必要）
    unreachable = []
    for file in all_files:
        if file not in reachable and file.name != '__init__.py':
            unreachable.append(file)
    
    return unreachable, import_graph

def main():
    """メイン処理"""
    print("未使用ファイルの分析を開始...")
    
    root_dir = Path(__file__).parent
    unused_files, import_graph = find_unused_files(root_dir)
    
    print(f"\n全ソースファイル数: {len(list(Path(root_dir / 'src').rglob('*.py')))}")
    print(f"未使用の可能性があるファイル数: {len(unused_files)}")
    
    if unused_files:
        print("\n未使用の可能性があるファイル:")
        for file in sorted(unused_files):
            relative_path = file.relative_to(root_dir)
            print(f"  - {relative_path}")
            
            # このファイルをインポートしているファイルがあるか確認
            importers = []
            for src, imports in import_graph.items():
                if file in imports:
                    importers.append(src)
            
            if importers:
                print(f"    （注: 以下のファイルからインポートされていますが、到達不可能）")
                for imp in importers[:3]:  # 最初の3つだけ表示
                    print(f"      - {imp.relative_to(root_dir)}")
                if len(importers) > 3:
                    print(f"      ... 他 {len(importers) - 3} ファイル")
    
    # カバレッジ0%のファイルとの比較
    print("\n\nカバレッジ0%のファイルとの比較:")
    coverage_zero_files = [
        'src/cli/__init__.py',
        'src/env_core/step/simple_graph_analysis.py',
        'src/env_core/types.py',
        'src/env_core/workflow/application/step_to_request_adapter.py',
        'src/env_core/workflow/domain/workflow_domain_service.py',
        'src/env_core/workflow/infrastructure/request_infrastructure_service.py',
        'src/env_core/workflow/layered_workflow_builder.py',
        'src/env_factories/request_builders.py',
        'src/env_integration/fitting/environment_inspector.py',
        'src/env_integration/fitting/preparation_planner.py',
        'src/environment/__init__.py',
        'src/factories/factory_coordinator.py',
        'src/infrastructure/__init__.py',
        'src/workflow/__init__.py',
    ]
    
    unused_paths = {str(f.relative_to(root_dir)) for f in unused_files}
    coverage_zero_set = set(coverage_zero_files)
    
    both = unused_paths & coverage_zero_set
    only_unused = unused_paths - coverage_zero_set
    only_zero_coverage = coverage_zero_set - unused_paths
    
    if both:
        print(f"\n未使用かつカバレッジ0%: {len(both)}ファイル")
        for f in sorted(both):
            print(f"  - {f}")
    
    if only_unused:
        print(f"\n未使用だがカバレッジあり: {len(only_unused)}ファイル")
        for f in sorted(only_unused):
            print(f"  - {f}")
    
    if only_zero_coverage:
        print(f"\nカバレッジ0%だが使用されている: {len(only_zero_coverage)}ファイル")
        for f in sorted(only_zero_coverage):
            print(f"  - {f}")

if __name__ == '__main__':
    main()