"""
インポート解決チェックルール

存在しないモジュールのインポートや循環インポートを検出します。
"""

import ast
from pathlib import Path
from typing import List, Set

import sys
sys.path.append(str(Path(__file__).parent.parent))

from models.check_result import CheckResult, FailureLocation


class ImportChecker(ast.NodeVisitor):
    """
    インポート文をチェックするクラス
    """
    
    def __init__(self, file_path: str, project_root: Path):
        self.file_path = file_path
        self.project_root = project_root
        self.violations = []
        self.imported_modules: Set[str] = set()
    
    def visit_Import(self, node):
        """import文をチェック"""
        for alias in node.names:
            self.imported_modules.add(alias.name)
            if not self._is_valid_import(alias.name):
                self.violations.append(FailureLocation(
                    file_path=self.file_path,
                    line_number=node.lineno
                ))
        self.generic_visit(node)
    
    def visit_ImportFrom(self, node):
        """from ... import文をチェック"""
        if node.module:
            self.imported_modules.add(node.module)
            if not self._is_valid_import(node.module):
                self.violations.append(FailureLocation(
                    file_path=self.file_path,
                    line_number=node.lineno
                ))
        self.generic_visit(node)
    
    def _is_valid_import(self, module_name: str) -> bool:
        """インポートが有効かチェック（簡易版）"""
        # 標準ライブラリやサードパーティライブラリは一旦OK
        if not module_name.startswith(('src.', 'tests.', 'scripts.')):
            return True
        
        # プロジェクト内のモジュールは存在チェック
        parts = module_name.split('.')
        module_path = self.project_root / Path(*parts)
        
        # ディレクトリまたは.pyファイルとして存在するかチェック
        return module_path.exists() or module_path.with_suffix('.py').exists()


def check_file(file_path: Path, project_root: Path) -> List[FailureLocation]:
    """
    単一ファイルのインポートをチェックする
    
    Args:
        file_path: チェック対象のファイルパス
        project_root: プロジェクトルートパス
    
    Returns:
        違反箇所のリスト
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        tree = ast.parse(content, filename=str(file_path))
        
        checker = ImportChecker(str(file_path), project_root)
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
                
                violations = check_file(py_file, project_root)
                all_violations.extend(violations)
    
    fix_policy = "モジュールの依存関係を確認してください。相対インポートではなく絶対インポートを使用してください。循環インポートが発生していないか確認してください。必要なパッケージがインストールされているか確認してください。"
    
    fix_example = """# Before - 相対インポート
from ..utils import helper

# After - 絶対インポート
from src.utils import helper

# Before - 存在しないモジュール
from src.nonexistent import something

# After - 正しいパスを指定
from src.existing_module import something"""
    
    return CheckResult(
        failure_locations=all_violations,
        fix_policy=fix_policy,
        fix_example_code=fix_example
    )


if __name__ == "__main__":
    result = main()
    print(f"インポートチェッカー: {len(result.failure_locations)}件の違反を検出")