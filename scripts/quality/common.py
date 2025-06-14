#!/usr/bin/env python3
"""
品質チェック共通機能
"""

import ast
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional


@dataclass(frozen=True)
class QualityIssue:
    """品質問題を表現する不変データ構造"""
    file: str
    line: int
    issue_type: str
    description: str
    severity: str
    details: str = ""


class BaseQualityChecker(ast.NodeVisitor):
    """品質チェックの基底クラス"""

    def __init__(self, filename: str, config: dict):
        self.filename = filename
        self.config = config
        self.issues: List[QualityIssue] = []

        # ファイルパスベースの分類
        self.is_test = self._is_test_file(filename)
        self.is_driver = 'drivers/' in filename
        self.is_domain = '/domain/' in filename
        self.is_excluded = self._check_exclusion(filename)

    def _is_test_file(self, filename: str) -> bool:
        """テストファイルかどうか判定"""
        return 'test_' in Path(filename).name or '/tests/' in filename

    def _check_exclusion(self, filename: str) -> bool:
        """除外パターンをチェック"""
        exclude_patterns = self.config.get('exclude_patterns', [])
        return any(Path(filename).match(pattern) for pattern in exclude_patterns)

    def add_issue(self, node: ast.AST, issue_type: str, description: str,
                  severity: str = "warning", details: str = "") -> None:
        """問題を追加"""
        if hasattr(node, 'lineno'):
            line = node.lineno
        else:
            line = 0

        self.issues.append(QualityIssue(
            file=self.filename,
            line=line,
            issue_type=issue_type,
            description=description,
            severity=severity,
            details=details
        ))

    def get_function_lines(self, node: ast.FunctionDef) -> int:
        """関数の行数を取得"""
        if hasattr(node, 'end_lineno') and node.end_lineno:
            return node.end_lineno - node.lineno + 1
        return len(ast.unparse(node).split('\n'))

    def format_issues(self) -> str:
        """問題をフォーマットして出力用文字列にする"""
        if not self.issues:
            return ""

        result = []
        for issue in self.issues:
            severity_symbol = {
                'error': '❌',
                'warning': '⚠️',
                'info': 'ℹ️'
            }.get(issue.severity, '⚠️')

            result.append(f"{severity_symbol} {Path(issue.file).name}:{issue.line} - {issue.description}")
            if issue.details:
                result.append(f"   詳細: {issue.details}")

        return '\n'.join(result)


def analyze_file_structure(file_path: str) -> dict:
    """ファイル構造を分析"""
    try:
        with open(file_path, encoding='utf-8') as f:
            content = f.read()

        tree = ast.parse(content, filename=file_path)

        return {
            'functions': [node.name for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)],
            'classes': [node.name for node in ast.walk(tree) if isinstance(node, ast.ClassDef)],
            'imports': [node.module for node in ast.walk(tree) if isinstance(node, ast.ImportFrom) and node.module],
            'lines': len(content.split('\n'))
        }
    except Exception:
        return {
            'functions': [],
            'classes': [],
            'imports': [],
            'lines': 0
        }


def find_python_files(directory: str, exclude_patterns: Optional[List[str]] = None) -> List[str]:
    """Pythonファイルを再帰的に検索"""
    if exclude_patterns is None:
        exclude_patterns = ['__pycache__', '.git', '.pytest_cache']

    files = []
    for path in Path(directory).rglob('*.py'):
        if not any(pattern in str(path) for pattern in exclude_patterns):
            files.append(str(path))

    return sorted(files)
