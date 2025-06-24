"""
Infrastructure重複生成チェックルール

Infrastructureコンポーネントの重複生成を検出します。
create_関数を複数回呼び出していないかチェックします。
"""

import ast
from pathlib import Path
from typing import List, Dict

import sys
sys.path.append(str(Path(__file__).parent.parent))

from models.check_result import CheckResult, FailureLocation


class InfrastructureDuplicationChecker(ast.NodeVisitor):
    """
    Infrastructure create関数の呼び出しをチェックするクラス
    """
    
    def __init__(self, file_path: str):
        self.file_path = file_path
        self.violations = []
        self.create_calls: Dict[str, int] = {}
    
    def visit_Call(self, node):
        """関数呼び出しをチェック"""
        func_name = self._get_function_name(node.func)
        
        # create_で始まる関数の呼び出しを検出
        if func_name and func_name.startswith('create_'):
            if func_name not in self.create_calls:
                self.create_calls[func_name] = 0
            self.create_calls[func_name] += 1
            
            # 2回目以降の呼び出しは違反
            if self.create_calls[func_name] > 1:
                self.violations.append(FailureLocation(
                    file_path=self.file_path,
                    line_number=node.lineno
                ))
        
        self.generic_visit(node)
    
    def _get_function_name(self, node) -> str:
        """関数名を取得"""
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            return node.attr
        return ''


def check_file(file_path: Path) -> List[FailureLocation]:
    """
    単一ファイルのInfrastructure重複生成をチェックする
    
    Args:
        file_path: チェック対象のファイルパス
    
    Returns:
        違反箇所のリスト
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        tree = ast.parse(content, filename=str(file_path))
        
        checker = InfrastructureDuplicationChecker(str(file_path))
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
    
    fix_policy = """Infrastructureコンポーネントの重複生成を避けてください。
シングルトンパターンまたは依存性注入を使用してください。
main.pyからの一元的な注入を実装してください。
リソースの適切な管理を行ってください。"""
    
    fix_example = """# Before - 重複生成
class Service1:
    def __init__(self):
        self.logger = create_logger(verbose=True, silent=False, system_operations=None)
        self.file_handler = create_file_handler(mock=False, file_operations=None)

class Service2:
    def __init__(self):
        self.logger = create_logger(verbose=True, silent=False, system_operations=None)  # 重複
        self.file_handler = create_file_handler(mock=False, file_operations=None)  # 重複

# After - main.pyからの一元的な注入
# main.py
from infrastructure.logger import create_logger
from infrastructure.file_handler import create_file_handler

# 一度だけ生成
logger = create_logger(verbose=True, silent=False, system_operations=None)
file_handler = create_file_handler(mock=False, file_operations=None)

# 依存性注入
service1 = Service1(logger, file_handler)
service2 = Service2(logger, file_handler)

# Service側
class Service1:
    def __init__(self, logger, file_handler):
        self.logger = logger
        self.file_handler = file_handler

class Service2:
    def __init__(self, logger, file_handler):
        self.logger = logger
        self.file_handler = file_handler"""
    
    return CheckResult(
        failure_locations=all_violations,
        fix_policy=fix_policy,
        fix_example_code=fix_example
    )


if __name__ == "__main__":
    result = main()
    print(f"Infrastructure重複生成チェッカー: {len(result.failure_locations)}件の違反を検出")