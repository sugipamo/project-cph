import ast
from pathlib import Path
from typing import List
import sys
sys.path.append(str(Path(__file__).parent.parent))
from models.check_result import CheckResult, FailureLocation

class DefaultValueChecker(ast.NodeVisitor):
    """関数の引数にデフォルト値が設定されているかをチェックする"""

    def __init__(self, file_path: str):
        self.file_path = file_path
        self.violations = []

    def visit_FunctionDef(self, node):
        for arg in node.args.defaults:
            self.violations.append(FailureLocation(file_path=self.file_path, line_number=node.lineno))
        for arg in node.args.kw_defaults:
            if arg is not None:
                self.violations.append(FailureLocation(file_path=self.file_path, line_number=node.lineno))
        self.generic_visit(node)

    def visit_AsyncFunctionDef(self, node):
        self.visit_FunctionDef(node)

def check_file(file_path: Path) -> List[FailureLocation]:
    """ファイルをチェックしてデフォルト値の使用箇所を検出"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        tree = ast.parse(content, filename=str(file_path))
        checker = DefaultValueChecker(str(file_path))
        checker.visit(tree)
        return checker.violations
    except Exception:
        return []

def main(di_container) -> CheckResult:
    """メインエントリーポイント"""
    project_root = Path(__file__).parent.parent.parent
    src_dir = project_root / 'src'
    all_violations = []
    if src_dir.exists():
        for py_file in src_dir.rglob('*.py'):
            violations = check_file(py_file)
            all_violations.extend(violations)
    fix_policy = '引数のデフォルト値を削除し、呼び出し元で明示的に値を渡すようにしてください。'
    fix_example = '# Before\ndef process_data(data, timeout=30):\n    # 処理\n\n# After\ndef process_data(data, timeout):\n    # 処理\n\n# 呼び出し元\nprocess_data(data, timeout=30)'
    return CheckResult(failure_locations=all_violations, fix_policy=fix_policy, fix_example_code=fix_example)
if __name__ == '__main__':
    result = main()
    print(f'Found {len(result.failure_locations)} violations')