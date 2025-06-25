"""
クリーンアーキテクチャチェックルール

レイヤー間の依存関係が正しい方向になっているかチェックします。
ドメイン層（operations）は外部依存を持ってはいけません。
"""
import ast
from pathlib import Path
from typing import List, Set
import sys
sys.path.append(str(Path(__file__).parent.parent))
from models.check_result import CheckResult, FailureLocation

class CleanArchitectureChecker(ast.NodeVisitor):
    """
    インポート文から依存関係をチェックするクラス
    """

    def __init__(self, file_path: str):
        self.file_path = file_path
        self.violations = []
        self.imports: Set[str] = set()

    def visit_Import(self, node):
        """import文をチェック"""
        for alias in node.names:
            self.imports.add(alias.name)
            if self._is_violation(alias.name):
                self.violations.append(FailureLocation(file_path=self.file_path, line_number=node.lineno))
        self.generic_visit(node)

    def visit_ImportFrom(self, node):
        """from ... import文をチェック"""
        if node.module:
            self.imports.add(node.module)
            if self._is_violation(node.module):
                self.violations.append(FailureLocation(file_path=self.file_path, line_number=node.lineno))
        self.generic_visit(node)

    def _is_violation(self, module_name: str) -> bool:
        """依存関係違反かチェック"""
        if 'operations' in self.file_path and 'infrastructure' in module_name:
            return True
        if 'operations' in self.file_path and 'requests' in module_name:
            return True
        if 'domain' in self.file_path and 'infrastructure' in module_name:
            return True
        return False

def check_file(file_path: Path) -> List[FailureLocation]:
    """
    単一ファイルのアーキテクチャ違反をチェックする
    
    Args:
        file_path: チェック対象のファイルパス
    
    Returns:
        違反箇所のリスト
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        tree = ast.parse(content, filename=str(file_path))
        checker = CleanArchitectureChecker(str(file_path))
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
    check_dirs = [project_root / 'src']
    for check_dir in check_dirs:
        if check_dir.exists():
            for py_file in check_dir.rglob('*.py'):
                if '__pycache__' in str(py_file):
                    continue
                violations = check_file(py_file)
                all_violations.extend(violations)
    fix_policy = '【CLAUDE.mdルール適用】\nレイヤー間の依存関係を正しい方向に修正してください。\nドメイン層（operations）は外部依存を持ってはいけません。\nインフラストラクチャ層への直接依存を避け、依存性注入を使用してください。\n循環依存を解消してください。\n例: src.operations -> src.infrastructure (×) / main.pyからの注入 (○)'
    fix_example = '# Before - ドメイン層からインフラ層への直接依存\n# src/operations/data_processor.py\nfrom src.infrastructure.file_handler import FileHandler  # 違反\n\nclass DataProcessor:\n    def process(self, file_path):\n        handler = FileHandler()\n        data = handler.read_file(file_path)\n        return self.transform(data)\n\n# After - 依存性注入を使用\n# src/operations/data_processor.py\nfrom src.shared.interfaces import FileHandlerInterface  # インターフェースに依存\n\nclass DataProcessor:\n    def __init__(self, file_handler: FileHandlerInterface):\n        self.file_handler = file_handler\n    \n    def process(self, file_path):\n        data = self.file_handler.read_file(file_path)\n        return self.transform(data)\n\n# src/shared/interfaces.py\nfrom abc import ABC, abstractmethod\n\nclass FileHandlerInterface(ABC):\n    @abstractmethod\n    def read_file(self, file_path: str) -> str:\n        pass\n\n# main.pyでの注入\nfrom src.infrastructure.file_handler import FileHandler\nfrom src.operations.data_processor import DataProcessor\n\nfile_handler = FileHandler()\nprocessor = DataProcessor(file_handler)'
    return CheckResult(failure_locations=all_violations, fix_policy=fix_policy, fix_example_code=fix_example)
if __name__ == '__main__':
    result = main()
    print(f'クリーンアーキテクチャチェッカー: {len(result.failure_locations)}件の違反を検出')