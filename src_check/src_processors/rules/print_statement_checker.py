import ast
from pathlib import Path
from typing import List

import sys
sys.path.append(str(Path(__file__).parent.parent))

from models.check_result import CheckResult, FailureLocation


class PrintStatementChecker(ast.NodeVisitor):
    """print文の使用をチェックする"""
    
    def __init__(self, file_path: str):
        self.file_path = file_path
        self.violations = []
    
    def visit_Call(self, node):
        if isinstance(node.func, ast.Name) and node.func.id == 'print':
            self.violations.append(FailureLocation(
                file_path=self.file_path,
                line_number=node.lineno
            ))
        
        self.generic_visit(node)


def check_file(file_path: Path) -> List[FailureLocation]:
    """ファイルをチェックしてprint文の使用箇所を検出"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        tree = ast.parse(content, filename=str(file_path))
        checker = PrintStatementChecker(str(file_path))
        checker.visit(tree)
        
        return checker.violations
    except Exception:
        return []


def main() -> CheckResult:
    """メインエントリーポイント"""
    project_root = Path(__file__).parent.parent.parent
    src_dir = project_root / "src"
    
    all_violations = []
    
    if src_dir.exists():
        for py_file in src_dir.rglob("*.py"):
            violations = check_file(py_file)
            all_violations.extend(violations)
    
    fix_policy = "print文の代わりにロギングライブラリ（logging）を使用してください。"
    
    fix_example = """# Before
print(f"Processing file: {filename}")

# After
import logging

logger = logging.getLogger(__name__)
logger.info(f"Processing file: {filename}")"""
    
    return CheckResult(
        failure_locations=all_violations,
        fix_policy=fix_policy,
        fix_example_code=fix_example
    )


if __name__ == "__main__":
    result = main()
    print(f"Found {len(result.failure_locations)} violations")