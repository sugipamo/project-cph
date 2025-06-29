"""
循環インポート・遅延インポートチェックルール

CLAUDE.mdに従い、循環インポートと遅延インポートを検出します。
"""
import ast
from pathlib import Path
from typing import List, Dict, Set, Optional
import sys
sys.path.append(str(Path(__file__).parent.parent))
from models.check_result import CheckResult, FailureLocation, LogLevel

class DelayedImportChecker(ast.NodeVisitor):
    """
    遅延インポート（関数内インポート）をチェックするクラス
    """
    
    def __init__(self, file_path: str):
        self.file_path = file_path
        self.violations = []
        self.in_function = False
        
    def visit_FunctionDef(self, node):
        """関数定義内のインポートをチェック"""
        old_in_function = self.in_function
        self.in_function = True
        self.generic_visit(node)
        self.in_function = old_in_function
        
    def visit_AsyncFunctionDef(self, node):
        """非同期関数定義内のインポートをチェック"""
        self.visit_FunctionDef(node)
        
    def visit_Import(self, node):
        """import文をチェック"""
        if self.in_function:
            self.violations.append(FailureLocation(file_path=self.file_path, line_number=node.lineno))
        self.generic_visit(node)
        
    def visit_ImportFrom(self, node):
        """from ... import文をチェック"""
        if self.in_function:
            self.violations.append(FailureLocation(file_path=self.file_path, line_number=node.lineno))
        self.generic_visit(node)

def check_delayed_imports(file_path: Path) -> List[FailureLocation]:
    """
    単一ファイルの遅延インポートをチェックする
    
    Args:
        file_path: チェック対象のファイルパス
    
    Returns:
        違反箇所のリスト
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        tree = ast.parse(content, filename=str(file_path))
        checker = DelayedImportChecker(str(file_path))
        checker.visit(tree)
        return checker.violations
    except SyntaxError:
        return []
    except Exception:
        return []

def build_import_graph(src_dir: Path) -> Dict[str, Set[str]]:
    """
    インポートグラフを構築する
    
    Args:
        src_dir: ソースディレクトリ
    
    Returns:
        モジュール名をキーとし、インポート先のセットを値とする辞書
    """
    import_graph = {}
    
    for py_file in src_dir.rglob('*.py'):
        if '__pycache__' in str(py_file):
            continue
            
        module_path = str(py_file.relative_to(src_dir.parent).with_suffix('')).replace('/', '.')
        imports = set()
        
        try:
            with open(py_file, 'r', encoding='utf-8') as f:
                content = f.read()
            tree = ast.parse(content, filename=str(py_file))
            
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        if alias.name.startswith('src.'):
                            imports.add(alias.name)
                elif isinstance(node, ast.ImportFrom):
                    if node.module and node.module.startswith('src.'):
                        imports.add(node.module)
                        
            import_graph[module_path] = imports
        except:
            pass
            
    return import_graph

def find_circular_imports(import_graph: Dict[str, Set[str]]) -> List[List[str]]:
    """
    循環インポートを検出する
    
    Args:
        import_graph: インポートグラフ
    
    Returns:
        循環インポートのパスのリスト
    """
    def dfs(module: str, path: List[str], visited: Set[str], rec_stack: Set[str]) -> List[List[str]]:
        visited.add(module)
        rec_stack.add(module)
        path.append(module)
        
        cycles = []
        
        for imported in import_graph.get(module, set()):
            if imported not in visited:
                cycles.extend(dfs(imported, path.copy(), visited, rec_stack))
            elif imported in rec_stack:
                cycle_start = path.index(imported)
                cycle = path[cycle_start:] + [imported]
                cycles.append(cycle)
                
        rec_stack.remove(module)
        return cycles
    
    visited = set()
    all_cycles = []
    
    for module in import_graph:
        if module not in visited:
            cycles = dfs(module, [], visited, set())
            all_cycles.extend(cycles)
            
    # 重複を除去
    unique_cycles = []
    seen = set()
    
    for cycle in all_cycles:
        normalized = tuple(sorted(cycle[:-1]))  # 最後の重複要素を除去してソート
        if normalized not in seen and len(normalized) > 1:
            seen.add(normalized)
            unique_cycles.append(list(cycle))
            
    return unique_cycles

def main() -> CheckResult:
    """
    メインエントリーポイント
    
    Returns:
        CheckResult: チェック結果
    """
    project_root = Path(__file__).parent.parent.parent
    src_dir = project_root / 'src'
    all_violations = []
    
    # 遅延インポートのチェック
    delayed_import_violations = []
    if src_dir.exists():
        for py_file in src_dir.rglob('*.py'):
            if '__pycache__' in str(py_file):
                continue
            violations = check_delayed_imports(py_file)
            delayed_import_violations.extend(violations)
    
    # 循環インポートのチェック
    circular_import_files = []
    if src_dir.exists():
        import_graph = build_import_graph(src_dir)
        circular_imports = find_circular_imports(import_graph)
        
        # 循環インポートに関わるファイルを特定
        for cycle in circular_imports:
            for module in cycle[:-1]:  # 最後の重複を除く
                file_path = src_dir.parent / module.replace('.', '/') + '.py'
                if file_path.exists():
                    circular_import_files.append(FailureLocation(file_path=str(file_path), line_number=1))
    
    # すべての違反をまとめる
    all_violations.extend(delayed_import_violations)
    all_violations.extend(circular_import_files)
    
    fix_policy = '【CLAUDE.mdルール違反】\n循環インポート・遅延インポートを検出しました。\n\n遅延インポート（関数内インポート）:\n- 短期的な解決策として使用されている可能性があります\n- モジュール構造を見直し、適切な依存関係に修正してください\n\n循環インポート:\n- 設計上の問題を示しています\n- 共通インターフェースの抽出や依存関係の逆転を検討してください'
    
    fix_example = '''# 遅延インポートの例（悪い例）
def process_data(data):
    # 循環インポートを回避するための遅延インポート
    from src.operations.processor import DataProcessor
    processor = DataProcessor()
    return processor.process(data)

# 修正例1: 依存性注入
def process_data(data, processor):
    return processor.process(data)

# 修正例2: インターフェースの使用
from abc import ABC, abstractmethod

class ProcessorInterface(ABC):
    @abstractmethod
    def process(self, data): pass

def process_data(data, processor: ProcessorInterface):
    return processor.process(data)

# 循環インポートの例（悪い例）
# module_a.py
from src.module_b import ClassB

class ClassA:
    def method(self):
        return ClassB()

# module_b.py
from src.module_a import ClassA

class ClassB:
    def method(self):
        return ClassA()

# 修正例: 共通インターフェースの抽出
# interfaces.py
from abc import ABC, abstractmethod

class InterfaceA(ABC):
    @abstractmethod
    def method(self): pass

class InterfaceB(ABC):
    @abstractmethod
    def method(self): pass

# module_a.py
from src.interfaces import InterfaceB

class ClassA:
    def __init__(self, b_instance: InterfaceB):
        self.b_instance = b_instance'''
    
    return CheckResult(
        title='circular_delayed_import_check',
        log_level=LogLevel.ERROR if all_violations else LogLevel.INFO,
        failure_locations=all_violations,
        fix_policy=fix_policy,
        fix_example_code=fix_example
    )

if __name__ == '__main__':
    result = main()
    print(f'循環インポート・遅延インポートチェッカー: {len(result.failure_locations)}件の違反を検出')
    if result.failure_locations:
        delayed_count = sum(1 for v in result.failure_locations if 'def ' not in str(v))
        circular_count = len(result.failure_locations) - delayed_count
        print(f'  - 遅延インポート: {delayed_count}件')
        print(f'  - 循環インポート関連: {circular_count}件')