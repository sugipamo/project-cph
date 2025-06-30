"""
Infrastructure重複生成チェックルール

Infrastructureコンポーネントの重複生成を検出します。
create_関数を複数回呼び出していないかチェックします。
"""
import ast
from pathlib import Path
from typing import List, Dict
import sys
sys.path.append(str(Path(__file__).parent.parent))
from models.check_result import CheckResult, FailureLocation

class InfrastructureDuplicationChecker(ast.NodeVisitor):
    """
    Infrastructure create関数の呼び出しをチェックするクラス
    """

    def __init__(self, file_path: str):
        self.file_path = file_path
        self.violations = []
        self.create_calls: Dict[str, int] = {}

    def visit_Call(self, node):
        """関数呼び出しをチェック"""
        func_name = self._get_function_name(node.func)
        if func_name and func_name.startswith('create_'):
            if func_name not in self.create_calls:
                self.create_calls[func_name] = 0
            self.create_calls[func_name] += 1
            if self.create_calls[func_name] > 1:
                self.violations.append(FailureLocation(file_path=self.file_path, line_number=node.lineno))
        self.generic_visit(node)

    def _get_function_name(self, node) -> str:
        """関数名を取得"""
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            return node.attr
        return ''

def check_file(file_path: Path) -> List[FailureLocation]:
    """
    単一ファイルのInfrastructure重複生成をチェックする
    
    Args:
        file_path: チェック対象のファイルパス
    
    Returns:
        違反箇所のリスト
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        tree = ast.parse(content, filename=str(file_path))
        checker = InfrastructureDuplicationChecker(str(file_path))
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
    fix_policy = 'Infrastructureコンポーネントの重複生成を避けてください。\nシングルトンパターンまたは依存性注入を使用してください。\nmain.pyからの一元的な注入を実装してください。\nリソースの適切な管理を行ってください。'
    fix_example = '# Before - 重複生成\nclass Service1:\n    def __init__(self):\n        self.print = create_print(verbose=True, silent=False, system_operations=None)\n        self.file_handler = create_file_handler(mock=False, file_operations=None)\n\nclass Service2:\n    def __init__(self):\n        self.print = create_print(verbose=True, silent=False, system_operations=None)  # 重複\n        self.file_handler = create_file_handler(mock=False, file_operations=None)  # 重複\n\n# After - main.pyからの一元的な注入\n# main.py\nfrom infrastructure.print import create_print\nfrom infrastructure.file_handler import create_file_handler\n\n# 一度だけ生成\nprint = create_print(verbose=True, silent=False, system_operations=None)\nfile_handler = create_file_handler(mock=False, file_operations=None)\n\n# 依存性注入\nservice1 = Service1(print, file_handler)\nservice2 = Service2(print, file_handler)\n\n# Service側\nclass Service1:\n    def __init__(self, print, file_handler):\n        self.print = print\n        self.file_handler = file_handler\n\nclass Service2:\n    def __init__(self, print, file_handler):\n        self.print = print\n        self.file_handler = file_handler'
    return CheckResult(failure_locations=all_violations, fix_policy=fix_policy, fix_example_code=fix_example)
if __name__ == '__main__':
    result = main()
    print(f'Infrastructure重複生成チェッカー: {len(result.failure_locations)}件の違反を検出')