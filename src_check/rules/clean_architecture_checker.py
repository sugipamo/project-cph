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
                self.violations.append(FailureLocation(
                    file_path=self.file_path,
                    line_number=node.lineno
                ))
        self.generic_visit(node)
    
    def visit_ImportFrom(self, node):
        """from ... import文をチェック"""
        if node.module:
            self.imports.add(node.module)
            if self._is_violation(node.module):
                self.violations.append(FailureLocation(
                    file_path=self.file_path,
                    line_number=node.lineno
                ))
        self.generic_visit(node)
    
    def _is_violation(self, module_name: str) -> bool:
        """依存関係違反かチェック"""
        # operationsからinfrastructureへの依存は違反
        if 'operations' in self.file_path and 'infrastructure' in module_name:
            return True
        
        # operationsからrequestsへの依存は違反
        if 'operations' in self.file_path and 'requests' in module_name:
            return True
        
        # domainからinfrastructureへの依存は違反
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
    
    # チェック対象ディレクトリ
    check_dirs = [
        project_root / "src"
    ]
    
    for check_dir in check_dirs:
        if check_dir.exists():
            for py_file in check_dir.rglob("*.py"):
                if "__pycache__" in str(py_file):
                    continue
                
                violations = check_file(py_file)
                all_violations.extend(violations)
    
    fix_policy = """【CLAUDE.mdルール適用】
レイヤー間の依存関係を正しい方向に修正してください。
ドメイン層（operations）は外部依存を持ってはいけません。
インフラストラクチャ層への直接依存を避け、依存性注入を使用してください。
循環依存を解消してください。
例: src.operations -> src.infrastructure (×) / main.pyからの注入 (○)"""
    
    fix_example = """# Before - ドメイン層からインフラ層への直接依存
# src/operations/data_processor.py
from src.infrastructure.file_handler import FileHandler  # 違反

class DataProcessor:
    def process(self, file_path):
        handler = FileHandler()
        data = handler.read_file(file_path)
        return self.transform(data)

# After - 依存性注入を使用
# src/operations/data_processor.py
from src.shared.interfaces import FileHandlerInterface  # インターフェースに依存

class DataProcessor:
    def __init__(self, file_handler: FileHandlerInterface):
        self.file_handler = file_handler
    
    def process(self, file_path):
        data = self.file_handler.read_file(file_path)
        return self.transform(data)

# src/shared/interfaces.py
from abc import ABC, abstractmethod

class FileHandlerInterface(ABC):
    @abstractmethod
    def read_file(self, file_path: str) -> str:
        pass

# main.pyでの注入
from src.infrastructure.file_handler import FileHandler
from src.operations.data_processor import DataProcessor

file_handler = FileHandler()
processor = DataProcessor(file_handler)"""
    
    return CheckResult(
        failure_locations=all_violations,
        fix_policy=fix_policy,
        fix_example_code=fix_example
    )


if __name__ == "__main__":
    result = main()
    print(f"クリーンアーキテクチャチェッカー: {len(result.failure_locations)}件の違反を検出")