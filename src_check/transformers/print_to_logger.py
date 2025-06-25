"""
print文をlogger変換するトランスフォーマー
"""
import ast
import os
import sys
from pathlib import Path
from typing import Set

sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
from src_check.models.check_result import CheckResult, FailureLocation


class PrintToLoggerTransformer(ast.NodeTransformer):
    """print文をlogger()呼び出しに変換するトランスフォーマー"""
    
    def __init__(self):
        self.changes_made = False
        self.needs_logger_import = False
        self.has_logger_variable = False
    
    def visit_Module(self, node):
        """モジュールレベルでlogger変数の存在を確認"""
        # 既存のlogger変数をチェック
        for child in ast.walk(node):
            if isinstance(child, ast.Assign):
                for target in child.targets:
                    if isinstance(target, ast.Name) and target.id == 'logger':
                        self.has_logger_variable = True
                        break
        
        # 変換を実行
        new_node = self.generic_visit(node)
        
        # logger変数が必要で、まだ存在しない場合は追加
        if self.needs_logger_import and not self.has_logger_variable:
            logger_assign = ast.Assign(
                targets=[ast.Name(id='logger', ctx=ast.Store())],
                value=ast.Call(
                    func=ast.Attribute(
                        value=ast.Name(id='di_container', ctx=ast.Load()),
                        attr='resolve',
                        ctx=ast.Load()
                    ),
                    args=[ast.Constant(value='logger')],
                    keywords=[]
                )
            )
            
            # main関数内の先頭に挿入
            for child in new_node.body:
                if isinstance(child, ast.FunctionDef) and child.name == 'main':
                    child.body.insert(0, logger_assign)
                    break
        
        return new_node
    
    def visit_Call(self, node):
        """print呼び出しをlogger呼び出しに変換"""
        if isinstance(node.func, ast.Name) and node.func.id == 'print':
            self.changes_made = True
            self.needs_logger_import = True
            
            # print() → logger() に変換
            new_node = ast.Call(
                func=ast.Name(id='logger', ctx=ast.Load()),
                args=node.args,
                keywords=node.keywords
            )
            return new_node
        
        return self.generic_visit(node)


def transform_file(file_path: Path) -> bool:
    """ファイルのprint文をlogger呼び出しに変換"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            source = f.read()
        
        tree = ast.parse(source)
        transformer = PrintToLoggerTransformer()
        new_tree = transformer.visit(tree)
        
        if transformer.changes_made:
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
    
    failure_locations = []
    
    # src_processors/配下のみを対象にする
    target_dirs = [
        current_dir / "src_check" / "src_processors"
    ]
    
    for target_dir in target_dirs:
        if target_dir.exists():
            for py_file in target_dir.rglob("*.py"):
                if py_file.name == "__init__.py":
                    continue
                if transform_file(py_file):
                    failure_locations.append(FailureLocation(
                        file_path=str(py_file),
                        line_number=0
                    ))
    
    return CheckResult(
        failure_locations=failure_locations,
        fix_policy="src_processors配下のprint文をlogger呼び出しに自動変換し、di_container.resolve('logger')を追加",
        fix_example_code="logger = di_container.resolve('logger')\nlogger(message)  # print(message)から変換"
    )