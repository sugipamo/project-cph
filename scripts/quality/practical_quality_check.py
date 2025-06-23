#!/usr/bin/env python3
"""
実用的な品質チェッカー
関数型プログラミングの原則を実用的なレベルで適用
"""

import ast
import glob
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import List

sys.path.insert(0, str(Path(__file__).parent.parent))

from infrastructure.file_operations import FileOperations
from infrastructure.system_operations import SystemOperations


@dataclass(frozen=True)
class QualityIssue:
    file: str
    line: int
    issue_type: str
    description: str
    severity: str


class PracticalQualityChecker(ast.NodeVisitor):
    """実用的な品質チェック"""

    def __init__(self, filename: str, config: dict):
        self.filename = filename
        self.config = config
        self.issues: List[QualityIssue] = []
        self.current_function = None

        # ファイルパスベースの除外チェック
        self.is_excluded = self._check_exclusion(filename)
        self.is_driver = 'drivers/' in filename
        self.is_test = 'test_' in filename or '/tests/' in filename
        self.is_domain = '/domain/' in filename

    def _check_exclusion(self, filename: str) -> bool:
        """除外パターンをチェック"""
        return any(Path(filename).match(pattern) for pattern in self.config['exclude_patterns'])

    def visit_FunctionDef(self, node: ast.FunctionDef):
        """関数定義をチェック"""
        if self.is_excluded:
            return

        old_function = self.current_function
        self.current_function = node.name

        # 関数サイズチェック（極端に大きい場合のみ警告）
        func_lines = node.end_lineno - node.lineno + 1 if node.end_lineno else 1

        # 極端に大きい関数のみ警告 (100行以上)
        if func_lines >= 100:
            severity = 'warning'
            self.issues.append(QualityIssue(
                file=self.filename,
                line=node.lineno,
                issue_type='function_size',
                description=f'関数 {node.name} が {func_lines} 行です (推奨: 100行未満)',
                severity=severity
            ))

        self.generic_visit(node)
        self.current_function = old_function

    def visit_Assign(self, node: ast.Assign):
        """代入文をチェック（ドメイン層でのみ、テストファイルは除外）"""
        if self.is_excluded or not self.is_domain or self.is_test:
            return

        # 属性への代入をチェック（実行関連の状態変更は許可）
        for target in node.targets:
            if isinstance(target, ast.Attribute) and isinstance(target.value, ast.Name) and target.value.id == 'self' and self.current_function != '__init__':
                # 実行関連の状態変更と設定関連の変更は許可
                allowed_execution_attrs = {'_executed', '_result', '_results', 'structure', 'name', '_start_time'}
                if target.attr not in allowed_execution_attrs:
                    self.issues.append(QualityIssue(
                        file=self.filename,
                        line=node.lineno,
                        issue_type='mutable_state',
                        description=f'ドメイン層での可変状態: self.{target.attr} への代入',
                        severity='warning'
                    ))

    def visit_Call(self, node: ast.Call):
        """関数呼び出しをチェック"""
        if self.is_excluded:
            return

        # ドメイン層での副作用チェック
        if self.is_domain and isinstance(node.func, ast.Name):
            side_effect_functions = {
                'print', 'open', 'write', 'subprocess'
            }
            if node.func.id in side_effect_functions:
                self.issues.append(QualityIssue(
                    file=self.filename,
                    line=node.lineno,
                    issue_type='side_effect',
                    description=f'ドメイン層での副作用: {node.func.id} の呼び出し',
                    severity='error'
                ))


def main(file_ops: FileOperations, system_ops: SystemOperations):
    """メイン処理"""
    # 設定ファイルを読み込み
    # 一時的にデフォルト設定を使用（YAML操作は未実装のため）
    config_path = Path('.functional_quality_config.json')
    if system_ops.path_exists(config_path):
        config = file_ops.load_json(config_path)
    else:
        # デフォルト設定
        config = {
            'exclude_patterns': [],
            'rules': {
                'function_size': {
                    'default_max_lines': 50,
                    'test_max_lines': 100
                }
            }
        }

    print("🎯 実用的品質チェック開始...")

    # Pythonファイルを検索
    python_files = glob.glob('src/**/*.py', recursive=True)
    python_files.extend(glob.glob('tests/**/*.py', recursive=True))

    all_issues = []

    for filepath in sorted(python_files):
        try:
            with open(filepath, encoding='utf-8') as f:
                content = f.read()

            tree = ast.parse(content)
            checker = PracticalQualityChecker(filepath, config)
            checker.visit(tree)
            all_issues.extend(checker.issues)

        except Exception as e:
            print(f"⚠️  {filepath} の解析中にエラー: {e}")

    # 結果表示
    error_count = sum(1 for issue in all_issues if issue.severity == 'error')
    warning_count = sum(1 for issue in all_issues if issue.severity == 'warning')

    if all_issues:
        print(f"\n📋 検出された問題 ({len(all_issues)} 件):\n")

        # エラーを先に表示
        errors = [i for i in all_issues if i.severity == 'error']
        if errors:
            print("❌ エラー:")
            for issue in errors[:10]:
                print(f"  {issue.file}:{issue.line} - {issue.description}")
            if len(errors) > 10:
                print(f"  ... 他 {len(errors) - 10} 件")
            print()

        # 警告を表示
        warnings = [i for i in all_issues if i.severity == 'warning']
        if warnings:
            print("⚠️  警告:")
            for issue in warnings[:10]:
                print(f"  {issue.file}:{issue.line} - {issue.description}")
            if len(warnings) > 10:
                print(f"  ... 他 {len(warnings) - 10} 件")

    print("\n📊 チェック結果:")
    print(f"  ❌ エラー: {error_count}")
    print(f"  ⚠️  警告: {warning_count}")
    print(f"  📁 チェック済みファイル: {len(python_files)}")

    if error_count > 0:
        print("\n💥 重要なエラーが見つかりました。")
        system_ops.exit(1)
    elif warning_count > 50:  # 警告は50件まで許容
        print("\n⚠️  警告が多数あります。段階的な改善を推奨します。")
        system_ops.exit(0)
    else:
        print("\n✅ 実用的な品質基準をクリアしています！")
        system_ops.exit(0)


if __name__ == "__main__":
    import json
    import os
    import sys

    from infrastructure.file_operations_impl import FileOperationsImpl
    from infrastructure.system_operations_impl import SystemOperationsImpl

    # 依存性注入用のプロバイダーを作成
    class JSONProvider:
        def load(self, file_path):
            with open(file_path, encoding='utf-8') as f:
                return json.load(f)
        def dump(self, data, file_path, indent=2):
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=indent, ensure_ascii=False)

    class OSProvider:
        def getcwd(self): return os.getcwd()
        def chdir(self, path): os.chdir(path)
        def path_exists(self, path): return os.path.exists(path)
        def isfile(self, path): return os.path.isfile(path)
        def isdir(self, path): return os.path.isdir(path)
        def makedirs(self, path, exist_ok): os.makedirs(path, exist_ok=exist_ok)
        def remove(self, path): os.remove(path)
        def rmdir(self, path): os.rmdir(path)
        def listdir(self, path): return os.listdir(path)
        def get_env(self, key): return os.environ.get(key)
        def set_env(self, key, value): os.environ[key] = value

    class SysProvider:
        def exit(self, code): sys.exit(code)
        def get_argv(self): return sys.argv

    # SystemOperationsのshutil機能用のダミー
    class SystemOpsWithShutil:
        def __init__(self, os_provider, sys_provider):
            self._os_provider = os_provider
            self._sys_provider = sys_provider
        def get_cwd(self): return self._os_provider.getcwd()
        def chdir(self, path): self._os_provider.chdir(path)
        def path_exists(self, path): return self._os_provider.path_exists(path)
        def is_file(self, path): return self._os_provider.isfile(path)
        def is_dir(self, path): return self._os_provider.isdir(path)
        def makedirs(self, path, exist_ok): self._os_provider.makedirs(path, exist_ok)
        def remove(self, path): self._os_provider.remove(path)
        def rmdir(self, path): self._os_provider.rmdir(path)
        def listdir(self, path): return self._os_provider.listdir(path)
        def get_env(self, key, default): return self._os_provider.get_env(key, default)
        def set_env(self, key, value): self._os_provider.set_env(key, value)
        def exit(self, code): self._sys_provider.exit(code)
        def get_argv(self): return self._sys_provider.get_argv()

    file_ops = FileOperationsImpl(JSONProvider(), SystemOpsWithShutil(OSProvider(), SysProvider()))
    system_ops = SystemOperationsImpl(OSProvider(), SysProvider())
    main(file_ops, system_ops)
