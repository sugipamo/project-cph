"""
main()関数をmain(di_container)に変換するトランスフォーマー
"""
import ast
import os
import sys
from pathlib import Path
from typing import Set

sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
from src_check.models.check_result import CheckResult, FailureLocation


class MainFunctionConverter(ast.NodeTransformer):
    """main()関数にdi_container引数を追加するトランスフォーマー"""
    
    def __init__(self):
        self.changes_made = False
    
    def visit_FunctionDef(self, node):
        """関数定義をチェックしてmain関数を変換"""
        if node.name == 'main' and len(node.args.args) == 0:
            # main()関数にdi_container引数を追加
            di_container_arg = ast.arg(arg='di_container', annotation=None)
            node.args.args.append(di_container_arg)
            self.changes_made = True
        
        return self.generic_visit(node)
    
    def visit_AsyncFunctionDef(self, node):
        """非同期関数定義をチェックしてmain関数を変換"""
        if node.name == 'main' and len(node.args.args) == 0:
            # async main()関数にdi_container引数を追加
            di_container_arg = ast.arg(arg='di_container', annotation=None)
            node.args.args.append(di_container_arg)
            self.changes_made = True
        
        return self.generic_visit(node)


def convert_main_function(file_path: Path) -> bool:
    """ファイルのmain()関数をmain(di_container)に変換"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            source = f.read()
        
        tree = ast.parse(source)
        converter = MainFunctionConverter()
        new_tree = converter.visit(tree)
        
        if converter.changes_made:
            new_source = ast.unparse(new_tree)
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(new_source)
            return True
    except Exception:
        return False
    
    return False


def main(di_container) -> CheckResult:
    """メインエントリーポイント"""
    current_dir = Path(__file__).parent.parent.parent
    src_processors_path = current_dir / "src_check" / "src_processors"
    
    if not src_processors_path.exists():
        return CheckResult(
            failure_locations=[],
            fix_policy="src_processors directory not found",
            fix_example_code=None
        )
    
    failure_locations = []
    
    # src_processors配下の全ての.pyファイルを処理
    for py_file in src_processors_path.rglob("*.py"):
        if py_file.name == "__init__.py":
            continue
            
        if convert_main_function(py_file):
            failure_locations.append(FailureLocation(
                file_path=str(py_file),
                line_number=0
            ))
    
    return CheckResult(
        failure_locations=failure_locations,
        fix_policy="main()関数をmain(di_container)に自動変換",
        fix_example_code="def main(di_container) -> CheckResult:  # def main() -> CheckResult:から変換"
    )