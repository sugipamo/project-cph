"""
命名規則チェックルール

PEP 8に準拠した命名規則をチェックします。
"""
import ast
import re
from pathlib import Path
from typing import List
import sys
sys.path.append(str(Path(__file__).parent.parent))
from models.check_result import CheckResult, FailureLocation

class NamingChecker(ast.NodeVisitor):
    """
    命名規則をチェックするクラス
    """

    def __init__(self, file_path: str):
        self.file_path = file_path
        self.violations = []

    def visit_FunctionDef(self, node):
        """関数名をチェック（snake_case）"""
        if not self._is_snake_case(node.name) and (not node.name.startswith('_')):
            self.violations.append(FailureLocation(file_path=self.file_path, line_number=node.lineno))
        self.generic_visit(node)

    def visit_AsyncFunctionDef(self, node):
        """非同期関数名をチェック（snake_case）"""
        if not self._is_snake_case(node.name) and (not node.name.startswith('_')):
            self.violations.append(FailureLocation(file_path=self.file_path, line_number=node.lineno))
        self.generic_visit(node)

    def visit_ClassDef(self, node):
        """クラス名をチェック（PascalCase）"""
        if not self._is_pascal_case(node.name):
            self.violations.append(FailureLocation(file_path=self.file_path, line_number=node.lineno))
        self.generic_visit(node)

    def visit_Assign(self, node):
        """変数名をチェック（snake_case、定数はUPPER_CASE）"""
        for target in node.targets:
            if isinstance(target, ast.Name):
                if target.id.isupper():
                    if not self._is_upper_case(target.id):
                        self.violations.append(FailureLocation(file_path=self.file_path, line_number=node.lineno))
                elif not self._is_snake_case(target.id) and (not target.id.startswith('_')):
                    self.violations.append(FailureLocation(file_path=self.file_path, line_number=node.lineno))
        self.generic_visit(node)

    def _is_snake_case(self, name: str) -> bool:
        """snake_caseかチェック"""
        return bool(re.match('^[a-z_][a-z0-9_]*$', name))

    def _is_pascal_case(self, name: str) -> bool:
        """PascalCaseかチェック"""
        return bool(re.match('^[A-Z][a-zA-Z0-9]*$', name))

    def _is_upper_case(self, name: str) -> bool:
        """UPPER_CASEかチェック"""
        return bool(re.match('^[A-Z][A-Z0-9_]*$', name))

def check_file(file_path: Path) -> List[FailureLocation]:
    """
    単一ファイルの命名規則をチェックする
    
    Args:
        file_path: チェック対象のファイルパス
    
    Returns:
        違反箇所のリスト
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        tree = ast.parse(content, filename=str(file_path))
        checker = NamingChecker(str(file_path))
        checker.visit(tree)
        return checker.violations
    except SyntaxError:
        return []
    except Exception:
        return []

def main(di_container) -> CheckResult:
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
    fix_policy = 'PEP 8の命名規則に従ってください。変数名、関数名はsnake_caseを使用してください。クラス名はPascalCaseを使用してください。意味のある名前を使用し、略語は避けてください。'
    fix_example = '# Before - 不適切な命名\ndef calculateTotal(itemList):\n    TotalPrice = 0\n    for Item in itemList:\n        TotalPrice += Item.price\n    return TotalPrice\n\nclass user_account:\n    pass\n\n# After - PEP 8準拠の命名\ndef calculate_total(item_list):\n    total_price = 0\n    for item in item_list:\n        total_price += item.price\n    return total_price\n\nclass UserAccount:\n    pass\n\n# 定数の例\nMAX_RETRY_COUNT = 3\nDEFAULT_TIMEOUT = 30'
    return CheckResult(failure_locations=all_violations, fix_policy=fix_policy, fix_example_code=fix_example)
if __name__ == '__main__':
    result = main()
    logger(f'命名規則チェッカー: {len(result.failure_locations)}件の違反を検出')