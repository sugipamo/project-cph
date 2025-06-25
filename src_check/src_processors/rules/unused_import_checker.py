import ast
from pathlib import Path
from typing import List
import sys
sys.path.append(str(Path(__file__).parent.parent))
from models.check_result import CheckResult, FailureLocation

class UnusedImportChecker(ast.NodeVisitor):
    """未使用のインポートをチェックする"""

    def __init__(self, file_path: str):
        self.file_path = file_path
        self.imports = {}
        self.used_names = set()

    def visit_Import(self, node):
        for alias in node.names:
            name = alias.asname if alias.asname else alias.name
            self.imports[name] = node.lineno
        self.generic_visit(node)

    def visit_ImportFrom(self, node):
        for alias in node.names:
            name = alias.asname if alias.asname else alias.name
            self.imports[name] = node.lineno
        self.generic_visit(node)

    def visit_Name(self, node):
        if isinstance(node.ctx, ast.Load):
            self.used_names.add(node.id)
        self.generic_visit(node)

    def visit_Attribute(self, node):
        if isinstance(node.value, ast.Name):
            self.used_names.add(node.value.id)
        self.generic_visit(node)

    def get_unused_imports(self) -> List[FailureLocation]:
        unused = []
        for name, line_no in self.imports.items():
            if name not in self.used_names:
                unused.append(FailureLocation(file_path=self.file_path, line_number=line_no))
        return unused

def check_file(file_path: Path) -> List[FailureLocation]:
    """ファイルをチェックして未使用インポートを検出"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        tree = ast.parse(content, filename=str(file_path))
        checker = UnusedImportChecker(str(file_path))
        checker.visit(tree)
        return checker.get_unused_imports()
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
    fix_policy = '未使用のインポートを削除してください。'
    fix_example = "# Before\nimport os\nimport sys\nimport json  # 未使用\n\ndef process():\n    print(os.path.exists('file.txt'))\n    \n# After\nimport os\n\ndef process():\n    print(os.path.exists('file.txt'))"
    return CheckResult(failure_locations=all_violations, fix_policy=fix_policy, fix_example_code=fix_example)
if __name__ == '__main__':
    result = main()
    logger(f'Found {len(result.failure_locations)} violations')