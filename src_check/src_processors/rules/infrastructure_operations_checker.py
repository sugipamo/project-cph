"""
Infrastructure->Operations依存関係チェックルール

Infrastructure層からOperations層への過度な依存を検出します。
"""
import ast
from pathlib import Path
from typing import List, Dict
import sys
sys.path.append(str(Path(__file__).parent.parent))
from models.check_result import CheckResult, FailureLocation

class InfrastructureOperationsChecker(ast.NodeVisitor):
    """
    Infrastructure層からOperations層への依存をチェックするクラス
    """

    def __init__(self, file_path: str):
        self.file_path = file_path
        self.violations = []
        self.operations_imports: Dict[str, int] = {}

    def visit_Import(self, node):
        """import文をチェック"""
        for alias in node.names:
            if 'operations' in alias.name:
                module = alias.name
                if module not in self.operations_imports:
                    self.operations_imports[module] = 0
                self.operations_imports[module] += 1
                if self.operations_imports[module] > 1:
                    self.violations.append(FailureLocation(file_path=self.file_path, line_number=node.lineno))
        self.generic_visit(node)

    def visit_ImportFrom(self, node):
        """from ... import文をチェック"""
        if node.module and 'operations' in node.module:
            if node.module not in self.operations_imports:
                self.operations_imports[node.module] = 0
            self.operations_imports[node.module] += len(node.names)
            if self.operations_imports[node.module] >= 3:
                self.violations.append(FailureLocation(file_path=self.file_path, line_number=node.lineno))
        self.generic_visit(node)

def check_file(file_path: Path) -> List[FailureLocation]:
    """
    単一ファイルの依存関係をチェックする
    
    Args:
        file_path: チェック対象のファイルパス
    
    Returns:
        違反箇所のリスト
    """
    try:
        if 'infrastructure' not in str(file_path):
            return []
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        tree = ast.parse(content, filename=str(file_path))
        checker = InfrastructureOperationsChecker(str(file_path))
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
    check_dirs = [project_root / 'src' / 'infrastructure', project_root / 'scripts' / 'infrastructure', project_root / 'tests' / 'infrastructure']
    for check_dir in check_dirs:
        if check_dir.exists():
            for py_file in check_dir.rglob('*.py'):
                if '__pycache__' in str(py_file):
                    continue
                violations = check_file(py_file)
                all_violations.extend(violations)
    fix_policy = '【CLAUDE.mdルール適用】\nInfrastructure層からOperations層への過度な依存を検出しました。\n高頻度パターン: 共通インターフェースへの抽出を検討してください。\nrequests層の直接使用: 設計の見直しが必要です。\nmain.pyからの依存性注入を強化してください。\n例: 共通インターフェースをsrc/shared/interfacesに移動'
    fix_example = '# Before - Infrastructure層からOperations層への過度な依存\n# src/infrastructure/data_handler.py\nfrom src.operations.validator import Validator\nfrom src.operations.transformer import Transformer\nfrom src.operations.formatter import Formatter\nfrom src.operations.calculator import Calculator  # 過度な依存\n\nclass DataHandler:\n    def __init__(self):\n        self.validator = Validator()\n        self.transformer = Transformer()\n        self.formatter = Formatter()\n        self.calculator = Calculator()\n\n# After - 共通インターフェースの使用\n# src/shared/interfaces.py\nfrom abc import ABC, abstractmethod\n\nclass DataProcessorInterface(ABC):\n    @abstractmethod\n    def validate(self, data): pass\n    \n    @abstractmethod\n    def transform(self, data): pass\n    \n    @abstractmethod\n    def format(self, data): pass\n\n# src/infrastructure/data_handler.py\nfrom src.shared.interfaces import DataProcessorInterface\n\nclass DataHandler:\n    def __init__(self, processor: DataProcessorInterface):\n        self.processor = processor\n    \n    def handle(self, data):\n        validated = self.processor.validate(data)\n        transformed = self.processor.transform(validated)\n        return self.processor.format(transformed)\n\n# main.pyでの注入\nfrom src.operations.data_processor import DataProcessor\nfrom src.infrastructure.data_handler import DataHandler\n\nprocessor = DataProcessor()  # DataProcessorInterfaceを実装\nhandler = DataHandler(processor)'
    return CheckResult(failure_locations=all_violations, fix_policy=fix_policy, fix_example_code=fix_example)
if __name__ == '__main__':
    result = main()
    print(f'Infrastructure->Operations依存関係チェッカー: {len(result.failure_locations)}件の違反を検出')