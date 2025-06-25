"""
print文使用チェックルール

print文の使用を検出し、Loggerインターフェースの使用を推奨します。
"""
import ast
from pathlib import Path
from typing import List
import sys
sys.path.append(str(Path(__file__).parent.parent))
from models.check_result import CheckResult, FailureLocation

class PrintUsageChecker(ast.NodeVisitor):
    """
    print文の使用をチェックするクラス
    """

    def __init__(self, file_path: str):
        self.file_path = file_path
        self.violations = []

    def visit_Call(self, node):
        """関数呼び出しをチェック"""
        if isinstance(node.func, ast.Name) and node.func.id == 'print':
            self.violations.append(FailureLocation(file_path=self.file_path, line_number=node.lineno))
        self.generic_visit(node)

def check_file(file_path: Path) -> List[FailureLocation]:
    """
    単一ファイルのprint文使用をチェックする
    
    Args:
        file_path: チェック対象のファイルパス
    
    Returns:
        違反箇所のリスト
    """
    try:
        if 'infrastructure' in str(file_path):
            return []
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        tree = ast.parse(content, filename=str(file_path))
        checker = PrintUsageChecker(str(file_path))
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
    fix_policy = 'print文の代わりにLoggerインターフェースを使用してください。Infrastructure層から注入されたLoggerを使用してください。デバッグ用のprint文は本番コードから削除してください。必要な場合はprint()、logger.error()を使用してください。'
    fix_example = '# Before - print文の使用\ndef process_data(data):\n    print(f"Processing {len(data)} items")\n    result = transform(data)\n    print(f"Completed processing")\n    return result\n\n# After - Loggerインターフェースの使用\ndef process_data(data, logger):\n    print(f"Processing {len(data)} items")\n    result = transform(data)\n    print(f"Completed processing")\n    return result\n\n# main.pyでの依存性注入\nfrom infrastructure.logger import create_logger\n\nlogger = create_logger(verbose=True, silent=False, system_operations=None)\nresult = process_data(data, logger)'
    return CheckResult(failure_locations=all_violations, fix_policy=fix_policy, fix_example_code=fix_example)
if __name__ == '__main__':
    result = main()
    logger(f'print使用チェッカー: {len(result.failure_locations)}件の違反を検出')