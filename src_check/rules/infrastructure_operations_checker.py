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
                
                # 同じモジュールからの複数インポートは違反
                if self.operations_imports[module] > 1:
                    self.violations.append(FailureLocation(
                        file_path=self.file_path,
                        line_number=node.lineno
                    ))
        
        self.generic_visit(node)
    
    def visit_ImportFrom(self, node):
        """from ... import文をチェック"""
        if node.module and 'operations' in node.module:
            if node.module not in self.operations_imports:
                self.operations_imports[node.module] = 0
            self.operations_imports[node.module] += len(node.names)
            
            # 3つ以上のインポートは過度な依存
            if self.operations_imports[node.module] >= 3:
                self.violations.append(FailureLocation(
                    file_path=self.file_path,
                    line_number=node.lineno
                ))
        
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
        # infrastructureディレクトリ内のファイルのみチェック
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
    
    # チェック対象ディレクトリ（Infrastructureのみ）
    check_dirs = [
        project_root / "src" / "infrastructure",
        project_root / "scripts" / "infrastructure",
        project_root / "tests" / "infrastructure"
    ]
    
    for check_dir in check_dirs:
        if check_dir.exists():
            for py_file in check_dir.rglob("*.py"):
                if "__pycache__" in str(py_file):
                    continue
                
                violations = check_file(py_file)
                all_violations.extend(violations)
    
    fix_policy = """【CLAUDE.mdルール適用】
Infrastructure層からOperations層への過度な依存を検出しました。
高頻度パターン: 共通インターフェースへの抽出を検討してください。
requests層の直接使用: 設計の見直しが必要です。
main.pyからの依存性注入を強化してください。
例: 共通インターフェースをsrc/shared/interfacesに移動"""
    
    fix_example = """# Before - Infrastructure層からOperations層への過度な依存
# src/infrastructure/data_handler.py
from src.operations.validator import Validator
from src.operations.transformer import Transformer
from src.operations.formatter import Formatter
from src.operations.calculator import Calculator  # 過度な依存

class DataHandler:
    def __init__(self):
        self.validator = Validator()
        self.transformer = Transformer()
        self.formatter = Formatter()
        self.calculator = Calculator()

# After - 共通インターフェースの使用
# src/shared/interfaces.py
from abc import ABC, abstractmethod

class DataProcessorInterface(ABC):
    @abstractmethod
    def validate(self, data): pass
    
    @abstractmethod
    def transform(self, data): pass
    
    @abstractmethod
    def format(self, data): pass

# src/infrastructure/data_handler.py
from src.shared.interfaces import DataProcessorInterface

class DataHandler:
    def __init__(self, processor: DataProcessorInterface):
        self.processor = processor
    
    def handle(self, data):
        validated = self.processor.validate(data)
        transformed = self.processor.transform(validated)
        return self.processor.format(transformed)

# main.pyでの注入
from src.operations.data_processor import DataProcessor
from src.infrastructure.data_handler import DataHandler

processor = DataProcessor()  # DataProcessorInterfaceを実装
handler = DataHandler(processor)"""
    
    return CheckResult(
        failure_locations=all_violations,
        fix_policy=fix_policy,
        fix_example_code=fix_example
    )


if __name__ == "__main__":
    result = main()
    print(f"Infrastructure->Operations依存関係チェッカー: {len(result.failure_locations)}件の違反を検出")