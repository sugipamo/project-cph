"""
**kwargs automatic removal script for src_check auto_currect
"""
import ast
import os
import sys
from pathlib import Path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
from src_check.models.check_result import CheckResult, FailureLocation

class KwargsRemover(ast.NodeTransformer):

    def __init__(self):
        self.changes_made = False

    def visit_FunctionDef(self, node):
        original_kwarg = node.args.kwarg
        if node.args.kwarg and node.args.kwarg.arg == 'kwargs':
            node.args.kwarg = None
            self.changes_made = True
        self.generic_visit(node)
        return node

    def visit_AsyncFunctionDef(self, node):
        original_kwarg = node.args.kwarg
        if node.args.kwarg and node.args.kwarg.arg == 'kwargs':
            node.args.kwarg = None
            self.changes_made = True
        self.generic_visit(node)
        return node

def remove_kwargs_from_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        source = f.read()
    try:
        tree = ast.parse(source)
        remover = KwargsRemover()
        new_tree = remover.visit(tree)
        if remover.changes_made:
            new_source = ast.unparse(new_tree)
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(new_source)
            return True
    except Exception:
        return False
    return False

def main(di_container):
    current_dir = Path(__file__).parent.parent.parent
    src_path = current_dir / 'src'
    if not src_path.exists():
        return CheckResult(failure_locations=[], fix_policy='src directory not found', fix_example_code=None)
    failure_locations = []
    for py_file in src_path.rglob('*.py'):
        if remove_kwargs_from_file(py_file):
            failure_locations.append(FailureLocation(file_path=str(py_file), line_number=0))
    return CheckResult(failure_locations=failure_locations, fix_policy='**kwargs parameters automatically removed from function definitions', fix_example_code='def func(param1, param2): pass  # **kwargs removed')
if __name__ == '__main__':
    main()