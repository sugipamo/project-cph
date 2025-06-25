"""
getattr()デフォルト値使用チェックルール

getattr()の第3引数（デフォルト値）の使用を検出します。
CLAUDE.mdルールに従い、フォールバック処理は禁止されています。
"""
import ast
from pathlib import Path
from typing import List
import sys
sys.path.append(str(Path(__file__).parent.parent))
from models.check_result import CheckResult, FailureLocation

class GetattrChecker(ast.NodeVisitor):
    """
    getattr()のデフォルト値使用をチェックするクラス
    """

    def __init__(self, file_path: str):
        self.file_path = file_path
        self.violations = []

    def visit_Call(self, node):
        """関数呼び出しをチェック"""
        if isinstance(node.func, ast.Name) and node.func.id == 'getattr':
            if len(node.args) >= 3:
                self.violations.append(FailureLocation(file_path=self.file_path, line_number=node.lineno))
        self.generic_visit(node)

def check_file(file_path: Path) -> List[FailureLocation]:
    """
    単一ファイルのgetattr()使用をチェックする
    
    Args:
        file_path: チェック対象のファイルパス
    
    Returns:
        違反箇所のリスト
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        tree = ast.parse(content, filename=str(file_path))
        checker = GetattrChecker(str(file_path))
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
    fix_policy = '【CLAUDE.mdルール適用】\ngetattr()のデフォルト値使用は禁止されています。\n属性の存在チェックを明示的に行ってください。\nhasattr()を使用して属性の存在を確認してください。\n必要なエラーを見逃すことを防ぐため、フォールバック処理は避けてください。'
    fix_example = '# Before - getattr()のデフォルト値使用\nclass Config:\n    timeout = 30\n\nconfig = Config()\nretry_count = getattr(config, \'retry_count\', 3)  # デフォルト値\nmax_connections = getattr(config, \'max_connections\', 10)\n\n# After - 明示的な属性チェック\nclass Config:\n    timeout = 30\n    retry_count = 3  # 必要な属性は明示的に定義\n    max_connections = 10\n\nconfig = Config()\n\n# 属性の存在を明示的にチェック\nif hasattr(config, \'retry_count\'):\n    retry_count = config.retry_count\nelse:\n    raise AttributeError("retry_count属性が設定されていません")\n\n# または、直接アクセスしてAttributeErrorを適切に処理\ntry:\n    retry_count = config.retry_count\nexcept AttributeError:\n    raise ConfigurationError("retry_count属性が必要です")'
    return CheckResult(failure_locations=all_violations, fix_policy=fix_policy, fix_example_code=fix_example)
if __name__ == '__main__':
    result = main()
    logger(f'getattr()デフォルト値使用チェッカー: {len(result.failure_locations)}件の違反を検出')