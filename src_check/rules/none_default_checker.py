"""
None引数初期値チェックルール

関数の引数にデフォルト値（特にNone）を指定することを検出します。
CLAUDE.mdルールに従い、引数にデフォルト値を指定することは禁止されています。
"""

import ast
from pathlib import Path
from typing import List

import sys
sys.path.append(str(Path(__file__).parent.parent))

from models.check_result import CheckResult, FailureLocation


class NoneDefaultChecker(ast.NodeVisitor):
    """
    関数の引数のデフォルト値をチェックするクラス
    """
    
    def __init__(self, file_path: str):
        self.file_path = file_path
        self.violations = []
    
    def visit_FunctionDef(self, node):
        """関数定義の引数をチェック"""
        self._check_defaults(node)
        self.generic_visit(node)
    
    def visit_AsyncFunctionDef(self, node):
        """非同期関数定義の引数をチェック"""
        self._check_defaults(node)
        self.generic_visit(node)
    
    def _check_defaults(self, node):
        """デフォルト引数をチェック"""
        # デフォルト値を持つ引数の数
        num_defaults = len(node.args.defaults)
        if num_defaults > 0:
            # デフォルト値は引数リストの末尾から対応
            args_with_defaults = node.args.args[-num_defaults:]
            
            for i, default in enumerate(node.args.defaults):
                # すべてのデフォルト値を違反として記録
                self.violations.append(FailureLocation(
                    file_path=self.file_path,
                    line_number=node.lineno
                ))
        
        # キーワードオンリー引数のデフォルト値もチェック
        for default in node.args.kw_defaults:
            if default is not None:
                self.violations.append(FailureLocation(
                    file_path=self.file_path,
                    line_number=node.lineno
                ))


def check_file(file_path: Path) -> List[FailureLocation]:
    """
    単一ファイルのデフォルト引数をチェックする
    
    Args:
        file_path: チェック対象のファイルパス
    
    Returns:
        違反箇所のリスト
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        tree = ast.parse(content, filename=str(file_path))
        
        checker = NoneDefaultChecker(str(file_path))
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
    
    # チェック対象ディレクトリ
    check_dirs = [
        project_root / "src",
        project_root / "tests",
        project_root / "scripts"
    ]
    
    for check_dir in check_dirs:
        if check_dir.exists():
            for py_file in check_dir.rglob("*.py"):
                if "__pycache__" in str(py_file):
                    continue
                
                violations = check_file(py_file)
                all_violations.extend(violations)
    
    fix_policy = """【CLAUDE.mdルール適用】
引数にデフォルト値を指定することは禁止されています。
呼び出し元で値を用意することを徹底してください。
全ての引数を明示的に渡すことで、バグの発見を容易にします。
設定値が必要な場合は設定ファイルから取得してください。"""
    
    fix_example = """# Before - デフォルト引数の使用
def process_data(data, timeout=30, retry_count=3, logger=None):
    if logger is None:
        logger = get_default_logger()
    # 処理
    
# After - 明示的な引数
def process_data(data, timeout, retry_count, logger):
    # 処理

# 呼び出し元での値の準備
from src.configuration.config_manager import ConfigManager

config_manager = ConfigManager(file_handler)
timeout = config_manager.get_value('processing.timeout')
retry_count = config_manager.get_value('processing.retry_count')
logger = create_logger(verbose=True, silent=False, system_operations=None)

process_data(data, timeout, retry_count, logger)"""
    
    return CheckResult(
        failure_locations=all_violations,
        fix_policy=fix_policy,
        fix_example_code=fix_example
    )


if __name__ == "__main__":
    result = main()
    print(f"None引数初期値チェッカー: {len(result.failure_locations)}件の違反を検出")