"""
**kwargs使用チェックルール

関数定義やメソッド定義での**kwargsの使用を検出します。
CLAUDE.mdルールに従い、明示的な引数定義を推奨します。
"""
import ast
from pathlib import Path
from typing import List
import sys
sys.path.append(str(Path(__file__).parent.parent))
from models.check_result import CheckResult, FailureLocation

class KwargsChecker(ast.NodeVisitor):
    """
    **kwargsの使用をチェックするクラス
    """

    def __init__(self, file_path: str):
        self.file_path = file_path
        self.violations = []

    def visit_FunctionDef(self, node):
        """関数定義をチェック"""
        self._check_kwargs(node)
        self.generic_visit(node)

    def visit_AsyncFunctionDef(self, node):
        """非同期関数定義をチェック"""
        self._check_kwargs(node)
        self.generic_visit(node)

    def _check_kwargs(self, node):
        """関数の引数をチェックして**kwargsの使用を検出"""
        if node.args.kwarg:
            self.violations.append(FailureLocation(file_path=self.file_path, line_number=node.lineno))

def check_file(file_path: Path) -> List[FailureLocation]:
    """
    単一ファイルの**kwargs使用をチェックする
    
    Args:
        file_path: チェック対象のファイルパス
    
    Returns:
        違反箇所のリスト
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        tree = ast.parse(content, filename=str(file_path))
        checker = KwargsChecker(str(file_path))
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
    fix_policy = '【CLAUDE.mdルール適用】\n**kwargsの使用は推奨されません。\n関数の引数は明示的に定義してください。\nこれにより、関数のインターフェースが明確になり、型ヒントも適用できます。'
    fix_example = "# Before - **kwargsを使用\ndef configure(**kwargs):\n    config = {}\n    for key, value in kwargs.items():\n        config[key] = value\n    return config\n\n# After - 明示的な引数定義\nfrom typing import Optional\n\ndef configure(\n    host: str,\n    port: int,\n    timeout: Optional[int] = None,\n    debug: bool = False\n):\n    config = {\n        'host': host,\n        'port': port,\n        'timeout': timeout,\n        'debug': debug\n    }\n    return config\n\n# またはデータクラスを使用\nfrom dataclasses import dataclass\n\n@dataclass\nclass Config:\n    host: str\n    port: int\n    timeout: Optional[int] = None\n    debug: bool = False\n\ndef configure(config: Config):\n    return config"
    return CheckResult(failure_locations=all_violations, fix_policy=fix_policy, fix_example_code=fix_example)
if __name__ == '__main__':
    result = main()
    print(f'**kwargsチェッカー: {len(result.failure_locations)}件の違反を検出')