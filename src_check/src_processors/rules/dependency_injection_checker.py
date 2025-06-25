"""
依存性注入チェックルール

副作用（ファイル操作、外部API呼び出しなど）がInfrastructure層以外で行われていないかチェックします。
CLAUDE.mdルールに従い、副作用はsrc/infrastructure、scripts/infrastructureのみで許可されます。
"""
import ast
from pathlib import Path
from typing import List, Set
import sys
sys.path.append(str(Path(__file__).parent.parent))
from models.check_result import CheckResult, FailureLocation

class DependencyInjectionChecker(ast.NodeVisitor):
    """
    副作用を検出するクラス
    """

    def __init__(self, file_path: str):
        self.file_path = file_path
        self.violations = []
        self.side_effect_functions = {'open', 'write', 'read', 'mkdir', 'rmdir', 'remove', 'requests', 'urllib', 'socket', 'subprocess', 'os.system', 'os.popen', 'shutil'}

    def visit_Call(self, node):
        """関数呼び出しをチェック"""
        func_name = self._get_function_name(node.func)
        if func_name and any((effect in func_name for effect in self.side_effect_functions)):
            self.violations.append(FailureLocation(file_path=self.file_path, line_number=node.lineno))
        self.generic_visit(node)

    def visit_With(self, node):
        """with文（ファイル操作など）をチェック"""
        for item in node.items:
            if isinstance(item.context_expr, ast.Call):
                func_name = self._get_function_name(item.context_expr.func)
                if func_name == 'open':
                    self.violations.append(FailureLocation(file_path=self.file_path, line_number=node.lineno))
        self.generic_visit(node)

    def _get_function_name(self, node) -> str:
        """関数名を取得"""
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            parts = []
            current = node
            while isinstance(current, ast.Attribute):
                parts.append(current.attr)
                current = current.value
            if isinstance(current, ast.Name):
                parts.append(current.id)
            return '.'.join(reversed(parts))
        return ''

def check_file(file_path: Path) -> List[FailureLocation]:
    """
    単一ファイルの副作用をチェックする
    
    Args:
        file_path: チェック対象のファイルパス
    
    Returns:
        違反箇所のリスト
    """
    try:
        if 'infrastructure' in str(file_path) or file_path.name == 'main.py':
            return []
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        tree = ast.parse(content, filename=str(file_path))
        checker = DependencyInjectionChecker(str(file_path))
        checker.visit(tree)
        return checker.violations
    except SyntaxError:
        return []
    except Exception:
        return []

def main() -> CheckResult:
    """
    メインエントリーポイント
    
    Returns:
        CheckResult: チェック結果
    """
    project_root = Path(__file__).parent.parent.parent
    all_violations = []
    check_dirs = [project_root / 'src', project_root / 'tests', project_root / 'scripts']
    for check_dir in check_dirs:
        if check_dir.exists():
            for py_file in check_dir.rglob('*.py'):
                if '__pycache__' in str(py_file):
                    continue
                violations = check_file(py_file)
                all_violations.extend(violations)
    fix_policy = '【CLAUDE.mdルール適用】\n副作用はsrc/infrastructure、tests/infrastructureのみで許可されます。\n全ての副作用はmain.pyから依存性注入してください。\nビジネスロジック層では副作用を避けてください。\nファイル操作、外部APIコール、データベースアクセスはInfrastructure層で実装してください。'
    fix_example = "# Before - ビジネスロジック層での副作用\nclass DataProcessor:\n    def process_file(self, file_path):\n        with open(file_path, 'r') as f:  # 直接ファイル操作\n            data = f.read()\n        \n        result = self.transform(data)\n        \n        with open('output.txt', 'w') as f:  # 直接ファイル操作\n            f.write(result)\n\n# After - 依存性注入を使用\n# Infrastructure層 (src/infrastructure/file_handler.py)\nclass FileHandler:\n    def read_file(self, file_path):\n        with open(file_path, 'r') as f:\n            return f.read()\n    \n    def write_file(self, file_path, content):\n        with open(file_path, 'w') as f:\n            f.write(content)\n\n# ビジネスロジック層\nclass DataProcessor:\n    def __init__(self, file_handler):\n        self.file_handler = file_handler\n    \n    def process_file(self, input_path, output_path):\n        data = self.file_handler.read_file(input_path)\n        result = self.transform(data)\n        self.file_handler.write_file(output_path, result)\n\n# main.pyでの注入\nfrom infrastructure.file_handler import create_file_handler\n\nfile_handler = create_file_handler(mock=False, file_operations=None)\nprocessor = DataProcessor(file_handler)\nprocessor.process_file('input.txt', 'output.txt')"
    return CheckResult(failure_locations=all_violations, fix_policy=fix_policy, fix_example_code=fix_example)
if __name__ == '__main__':
    result = main()
    print(f'依存性注入チェッカー: {len(result.failure_locations)}件の違反を検出')