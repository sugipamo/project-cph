#!/usr/bin/env python3
"""
**kwargs automatic removal script for src_check auto_currect
"""

import ast
import os
import sys
from pathlib import Path


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
    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        return False
    
    return False


def main():
    src_path = Path("src")
    if not src_path.exists():
        print("src directory not found")
        return
    
    modified_files = []
    
    for py_file in src_path.rglob("*.py"):
        if remove_kwargs_from_file(py_file):
            modified_files.append(str(py_file))
            print(f"Removed **kwargs from: {py_file}")
    
    if modified_files:
        print(f"\nModified {len(modified_files)} files")
    else:
        print("No **kwargs found to remove")


if __name__ == "__main__":
    main()