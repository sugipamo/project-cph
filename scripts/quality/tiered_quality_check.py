#!/usr/bin/env python3
"""
階層化品質チェッカー
コンテキストに応じて異なる品質基準を適用
"""

import ast
import glob
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List


@dataclass(frozen=True)
class QualityIssue:
    file: str
    line: int
    issue_type: str
    description: str
    severity: str  # ERROR, WARNING, INFO
    tier: str      # core_logic, business_logic, utility


class TieredQualityChecker(ast.NodeVisitor):
    """階層化品質チェック"""

    def __init__(self, filename: str, config: dict):
        self.filename = filename
        self.config = config
        self.issues: List[QualityIssue] = []
        self.current_function = None
        self.current_tier = None

        # ファイルパスベースの基本判定
        self.is_excluded = self._check_exclusion(filename)
        self.is_test = 'test_' in filename or '/tests/' in filename
        self.is_domain = '/domain/' in filename

    def _check_exclusion(self, filename: str) -> bool:
        """除外パターンをチェック"""
        return any(Path(filename).match(pattern) for pattern in self.config['exclude_patterns'])

    def _determine_quality_tier(self, function_name: str, file_path: str, node: ast.FunctionDef) -> str:
        """品質基準の階層を判定"""

        # コアロジック判定
        core_logic_patterns = [
            '_execute_core', 'classify_error', 'parse_user_input',
            'state_machine', 'pipeline', 'workflow'
        ]

        if any(pattern in function_name for pattern in core_logic_patterns):
            return 'core_logic'

        # 関数の複雑さによる判定
        complexity = self._calculate_complexity(node)
        if complexity > 10 and len(node.body) > 60:
            # 既に複雑な関数はコアロジック扱い
            return 'core_logic'

        # ユーティリティ判定
        if any(path in file_path for path in ['/utils/', '/helpers/', '/formatters/']):
            return 'utility'

        # ドライバー層の特別扱い
        if '/drivers/' in file_path:
            return 'business_logic'  # 標準的な基準を適用

        # デフォルト
        return 'business_logic'

    def _calculate_complexity(self, node: ast.FunctionDef) -> int:
        """循環複雑度の概算計算"""
        complexity = 1  # ベース複雑度

        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.While, ast.For, ast.ExceptHandler)):
                complexity += 1
            elif isinstance(child, ast.BoolOp):
                complexity += len(child.values) - 1

        return complexity

    def _get_tier_limits(self, tier: str) -> Dict[str, Any]:
        """階層別の制限値を取得"""
        tiers = {
            'core_logic': {
                'max_lines': 80,
                'max_complexity': 15,
                'require_docs': True,
                'error_threshold': 100,  # これを超えるとERROR
                'warning_threshold': 80
            },
            'business_logic': {
                'max_lines': 50,
                'max_complexity': 10,
                'require_docs': False,
                'error_threshold': 70,
                'warning_threshold': 50
            },
            'utility': {
                'max_lines': 30,
                'max_complexity': 5,
                'require_docs': False,
                'error_threshold': 40,
                'warning_threshold': 30
            }
        }
        return tiers[tier]

    def _determine_severity(self, line_count: int, tier: str) -> str:
        """違反の重要度を判定"""
        limits = self._get_tier_limits(tier)

        if line_count > limits['error_threshold']:
            return 'ERROR'
        if line_count > limits['warning_threshold']:
            return 'WARNING'
        return 'INFO'

    def visit_FunctionDef(self, node: ast.FunctionDef):
        """関数定義をチェック"""
        if self.is_excluded:
            return

        old_function = self.current_function
        self.current_function = node.name

        # 品質階層の判定
        self.current_tier = self._determine_quality_tier(node.name, self.filename, node)

        # 関数サイズチェック
        line_count = node.end_lineno - node.lineno + 1
        limits = self._get_tier_limits(self.current_tier)

        # テストファイルには緩い基準を適用
        if self.is_test:
            limits['max_lines'] = min(limits['max_lines'] * 2, 100)

        severity = self._determine_severity(line_count, self.current_tier)

        if line_count > limits['max_lines']:
            self.issues.append(QualityIssue(
                file=self.filename,
                line=node.lineno,
                issue_type='function_size',
                description=f'関数 {node.name} が {line_count} 行です (推奨: {limits["max_lines"]}行以下, 階層: {self.current_tier})',
                severity=severity,
                tier=self.current_tier
            ))

        # 複雑度チェック
        complexity = self._calculate_complexity(node)
        if complexity > limits['max_complexity']:
            complexity_severity = 'WARNING' if self.current_tier == 'core_logic' else 'ERROR'
            self.issues.append(QualityIssue(
                file=self.filename,
                line=node.lineno,
                issue_type='complexity',
                description=f'関数 {node.name} の複雑度が {complexity} です (推奨: {limits["max_complexity"]}以下)',
                severity=complexity_severity,
                tier=self.current_tier
            ))

        # 文書化チェック
        if limits['require_docs'] and not ast.get_docstring(node):
            self.issues.append(QualityIssue(
                file=self.filename,
                line=node.lineno,
                issue_type='missing_docs',
                description=f'コアロジック関数 {node.name} にドキュメントが必要です',
                severity='WARNING',
                tier=self.current_tier
            ))

        self.generic_visit(node)
        self.current_function = old_function

    def visit_Assign(self, node: ast.Assign):
        """代入文をチェック（ドメイン層でのみ）"""
        if self.is_excluded or not self.is_domain:
            return

        # コアロジック層では可変状態を許可
        if self.current_tier == 'core_logic':
            return

        # 属性への代入をチェック
        for target in node.targets:
            if isinstance(target, ast.Attribute) and isinstance(target.value, ast.Name) and target.value.id == 'self' and self.current_function != '__init__':
                self.issues.append(QualityIssue(
                    file=self.filename,
                    line=node.lineno,
                    issue_type='mutable_state',
                    description=f'ドメイン層での可変状態: self.{target.attr} への代入',
                    severity='WARNING',
                    tier=self.current_tier or 'business_logic'
                ))


def analyze_file(filepath: str, config: dict) -> List[QualityIssue]:
    """ファイルを解析して品質問題を検出"""
    try:
        with open(filepath, encoding='utf-8') as f:
            content = f.read()

        tree = ast.parse(content, filename=filepath)
        checker = TieredQualityChecker(filepath, config)
        checker.visit(tree)

        return checker.issues

    except (UnicodeDecodeError, SyntaxError) as e:
        return [QualityIssue(
            file=filepath,
            line=1,
            issue_type='parse_error',
            description=f'ファイル解析エラー: {e}',
            severity='ERROR',
            tier='unknown'
        )]


def main():
    """メイン実行関数"""
    config = {
        'exclude_patterns': [
            '**/migrations/**',
            '**/venv/**',
            '**/node_modules/**',
            '**/__pycache__/**',
            '**/.*'
        ]
    }

    # Python ファイルを検索
    python_files = []
    for pattern in ['src/**/*.py', 'tests/**/*.py']:
        python_files.extend(glob.glob(pattern, recursive=True))

    all_issues = []
    error_count = 0
    warning_count = 0
    info_count = 0

    print("🎯 階層化品質チェック開始...")

    for filepath in python_files:
        issues = analyze_file(filepath, config)
        all_issues.extend(issues)

    if all_issues:
        print(f"\n📋 検出された問題 ({len(all_issues)} 件):\n")

        # 重要度別に集計・表示
        for severity in ['ERROR', 'WARNING', 'INFO']:
            severity_issues = [issue for issue in all_issues if issue.severity == severity]
            if severity_issues:
                if severity == 'ERROR':
                    print("❌ エラー:")
                    error_count = len(severity_issues)
                elif severity == 'WARNING':
                    print("⚠️  警告:")
                    warning_count = len(severity_issues)
                else:
                    print("ℹ️  情報:")
                    info_count = len(severity_issues)

                for issue in severity_issues[:20]:  # 最初の20件のみ表示
                    print(f"  {issue.file}:{issue.line} - {issue.description} (階層: {issue.tier})")

                if len(severity_issues) > 20:
                    print(f"  ... 他 {len(severity_issues) - 20} 件")
                print()

    # サマリー
    checked_files = len([f for f in python_files if not any(Path(f).match(p) for p in config['exclude_patterns'])])
    print("📊 チェック結果:")
    print(f"  ❌ エラー: {error_count}")
    print(f"  ⚠️  警告: {warning_count}")
    print(f"  ℹ️  情報: {info_count}")
    print(f"  📁 チェック済みファイル: {checked_files}")

    if error_count > 0:
        print("\n💥 重要なエラーが見つかりました。")
        print("品質基準の修正が必要です")
        return 1
    if warning_count > 0:
        print("\n⚠️ 警告があります。品質改善を推奨します。")
        return 0
    print("\n✅ 品質チェック完了。問題は見つかりませんでした。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
