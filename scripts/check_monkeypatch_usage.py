#!/usr/bin/env python3
"""
monkeypatch使用検出スクリプト

このスクリプトは、プロジェクト内でpytestのmonkeypatchフィクスチャの使用を検出します。
unittest.mockへの移行を推奨します。
"""

import ast
import sys
from pathlib import Path
from typing import List, Tuple


class MonkeypatchVisitor(ast.NodeVisitor):
    """ASTを走査してmonkeypatchの使用を検出"""
    
    def __init__(self, filename: str):
        self.filename = filename
        self.issues: List[Tuple[int, str]] = []
        
    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        """関数定義をチェック"""
        # 引数にmonkeypatchがあるかチェック
        for arg in node.args.args:
            if arg.arg == "monkeypatch":
                self.issues.append((
                    node.lineno,
                    f"Function '{node.name}' uses monkeypatch fixture"
                ))
        
        # 関数内のmonkeypatch使用をチェック
        for child in ast.walk(node):
            if isinstance(child, ast.Attribute):
                if (isinstance(child.value, ast.Name) and 
                    child.value.id == "monkeypatch"):
                    self.issues.append((
                        child.lineno,
                        f"monkeypatch.{child.attr} used"
                    ))
        
        self.generic_visit(node)


def check_file(filepath: Path) -> List[Tuple[str, int, str]]:
    """ファイルをチェックしてmonkeypatch使用を検出"""
    try:
        content = filepath.read_text(encoding='utf-8')
        tree = ast.parse(content, filename=str(filepath))
        visitor = MonkeypatchVisitor(str(filepath))
        visitor.visit(tree)
        
        return [(str(filepath), line, msg) for line, msg in visitor.issues]
    except Exception as e:
        print(f"Error processing {filepath}: {e}", file=sys.stderr)
        return []


def main():
    """メイン処理"""
    project_root = Path(__file__).parent.parent
    test_files = list(project_root.glob("tests/**/*.py"))
    test_files.extend(list(project_root.glob("tests_slow/**/*.py")))
    
    all_issues = []
    
    for test_file in test_files:
        issues = check_file(test_file)
        all_issues.extend(issues)
    
    if all_issues:
        print("❌ monkeypatch使用が検出されました:")
        print("-" * 80)
        
        # ファイルごとにグループ化
        by_file = {}
        for filepath, line, msg in all_issues:
            if filepath not in by_file:
                by_file[filepath] = []
            by_file[filepath].append((line, msg))
        
        for filepath, issues in by_file.items():
            print(f"\n📄 {filepath}")
            for line, msg in sorted(issues):
                print(f"  Line {line}: {msg}")
        
        print("\n" + "-" * 80)
        print("💡 推奨: unittest.mock.patchを使用してください")
        print("例:")
        print("  with unittest.mock.patch('module.Class.method', return_value=...):")
        print("      # テストコード")
        
        return 1
    else:
        print("✅ monkeypatchの使用は検出されませんでした")
        return 0


if __name__ == "__main__":
    sys.exit(main())