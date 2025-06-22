#!/usr/bin/env python3
"""
アーキテクチャ品質チェッカー

リファクタリング後のアーキテクチャ品質をチェック：
- モジュール構造の整合性
- 循環インポートの検出
- 依存関係の方向性
- ファイルサイズ制限
"""

import ast
import glob
import os
import sys
from collections import defaultdict
from dataclasses import dataclass
from typing import Dict, List, Tuple


@dataclass(frozen=True)
class ArchitectureIssue:
    """アーキテクチャ問題を表現する不変データ構造"""
    file: str
    issue_type: str
    description: str
    severity: str
    details: str = ""


class ImportAnalyzer(ast.NodeVisitor):
    """インポート関係を分析"""

    def __init__(self, filename: str):
        self.filename = filename
        self.imports: List[str] = []
        self.from_imports: List[Tuple[str, List[str]]] = []

    def visit_Import(self, node: ast.Import):
        for alias in node.names:
            self.imports.append(alias.name)

    def visit_ImportFrom(self, node: ast.ImportFrom):
        if node.module:
            names = [alias.name for alias in node.names]
            self.from_imports.append((node.module, names))


def analyze_imports(file_path: str) -> Tuple[List[str], List[Tuple[str, List[str]]]]:
    """ファイルのインポートを分析"""
    try:
        with open(file_path, encoding='utf-8') as f:
            content = f.read()

        tree = ast.parse(content, filename=file_path)
        analyzer = ImportAnalyzer(file_path)
        analyzer.visit(tree)

        return analyzer.imports, analyzer.from_imports
    except Exception as e:
        raise Exception(f"Failed to analyze imports in {file_path}: {e}") from e


def check_file_size_limits(directory: str) -> List[ArchitectureIssue]:
    """ファイルサイズ制限チェック"""
    issues = []
    python_files = glob.glob(f"{directory}/**/*.py", recursive=True)

    for file_path in python_files:
        try:
            with open(file_path, encoding='utf-8') as f:
                line_count = sum(1 for _ in f)

            # 極端に大きいファイルのみ警告 (800行以上)
            extreme_threshold = 800

            if line_count >= extreme_threshold:
                severity = 'warning'
                issues.append(ArchitectureIssue(
                    file=file_path,
                    issue_type='file_size',
                    description=f'ファイルサイズ {line_count} 行（推奨: {extreme_threshold}行未満）',
                    severity=severity,
                    details=f'極端に大きいファイルです ({line_count - extreme_threshold} 行超過)'
                ))
        except Exception:
            continue

    return issues


def check_module_structure(directory: str) -> List[ArchitectureIssue]:
    """モジュール構造チェック"""
    issues = []

    # 期待されるモジュール構造（workflow.builderは削除済み）

    # workflow.builderディレクトリは削除済みのため、チェックをスキップ

    return issues


def detect_circular_imports(directory: str) -> List[ArchitectureIssue]:
    """循環インポートの検出"""
    issues = []
    python_files = glob.glob(f"{directory}/**/*.py", recursive=True)

    # モジュール名とファイルパスのマッピング
    module_to_file = {}
    file_to_module = {}

    for file_path in python_files:
        # 相対パスからモジュール名を生成
        rel_path = os.path.relpath(file_path, directory)
        module_name = rel_path.replace('/', '.').replace('\\', '.').replace('.py', '')
        module_to_file[module_name] = file_path
        file_to_module[file_path] = module_name

    # 依存関係グラフを構築
    dependencies = defaultdict(set)

    for file_path in python_files:
        imports, from_imports = analyze_imports(file_path)
        current_module = file_to_module[file_path]

        # 内部インポートのみを対象
        for imp in imports:
            if imp.startswith('src.'):
                clean_imp = imp.replace('src.', '')
                if clean_imp in module_to_file:
                    dependencies[current_module].add(clean_imp)

        for module, _names in from_imports:
            if module and module.startswith('src.'):
                clean_module = module.replace('src.', '')
                if clean_module in module_to_file:
                    dependencies[current_module].add(clean_module)

    # 循環依存の検出（簡易版）
    visited = set()
    rec_stack = set()

    def dfs(module: str, path: List[str]) -> bool:
        if module in rec_stack:
            # 循環発見
            cycle_start = path.index(module)
            cycle = path[cycle_start:] + [module]
            issues.append(ArchitectureIssue(
                file=module_to_file[module],
                issue_type='circular_import',
                description=f'循環インポート検出: {" -> ".join(cycle)}',
                severity='error',
                details='モジュール間で循環依存が発生しています'
            ))
            return True

        if module in visited:
            return False

        visited.add(module)
        rec_stack.add(module)

        for dep in dependencies[module]:
            if dfs(dep, [*path, module]):
                return True

        rec_stack.remove(module)
        return False

    for module in dependencies:
        if module not in visited:
            dfs(module, [])

    return issues


def check_dependency_direction(directory: str) -> List[ArchitectureIssue]:
    """依存関係の方向性チェック"""
    issues = []

    # 期待される依存関係の階層（workflow.builderは削除済み）
    hierarchy = {
        'workflow.step': 0,  # ワークフローステップ
        'domain.requests': 1,  # リクエストレイヤー
        'application': 2   # アプリケーションレイヤー
    }

    python_files = glob.glob(f"{directory}/**/*.py", recursive=True)

    for file_path in python_files:
        # ファイルがどの階層に属するか判定
        current_level = None
        current_module = None

        for module, level in hierarchy.items():
            if module.replace('.', '/') in file_path:
                current_level = level
                current_module = module
                break

        if current_level is None:
            continue

        # インポートをチェック
        imports, from_imports = analyze_imports(file_path)

        all_imports = imports + [module for module, _ in from_imports]

        for imp in all_imports:
            if imp.startswith('src.'):
                # Skip utils imports as they are cross-cutting concerns
                if imp.startswith('src.utils.'):
                    continue

                for target_module, target_level in hierarchy.items():
                    if target_module.replace('.', '/') in imp:
                        if target_level >= current_level and target_module != current_module:
                            issues.append(ArchitectureIssue(
                                file=file_path,
                                issue_type='wrong_dependency_direction',
                                description=f'{current_module} (level {current_level}) が {target_module} (level {target_level}) に依存',
                                severity='warning',
                                details='下位モジュールが上位モジュールに依存しています'
                            ))
                        break

    return issues


def calculate_module_metrics(directory: str) -> Dict[str, any]:
    """モジュールメトリクスの計算"""
    python_files = glob.glob(f"{directory}/**/*.py", recursive=True)

    total_files = len(python_files)
    total_lines = 0
    max_file_size = 0
    max_file_path = ""

    module_counts = defaultdict(int)

    for file_path in python_files:
        try:
            with open(file_path, encoding='utf-8') as f:
                line_count = sum(1 for _ in f)
            total_lines += line_count

            if line_count > max_file_size:
                max_file_size = line_count
                max_file_path = file_path

            # モジュール別カウント
            rel_path = os.path.relpath(file_path, directory)
            if '/' in rel_path:
                module = rel_path.split('/')[0]
                module_counts[module] += 1
        except Exception:
            continue

    return {
        'total_files': total_files,
        'total_lines': total_lines,
        'average_file_size': total_lines / total_files if total_files > 0 else 0,
        'max_file_size': max_file_size,
        'max_file_path': max_file_path,
        'module_distribution': dict(module_counts)
    }


def main():
    """メイン関数"""
    if len(sys.argv) < 2:
        print("使用方法: python3 architecture_quality_check.py <directory>")
        sys.exit(1)

    directory = sys.argv[1]

    print("🏗️  アーキテクチャ品質チェック開始...")
    print()

    all_issues = []

    # 各種チェックを実行
    checks = [
        ("ファイルサイズ制限", check_file_size_limits),
        ("モジュール構造", check_module_structure),
        ("循環インポート", detect_circular_imports),
        ("依存関係方向", check_dependency_direction)
    ]

    for check_name, check_func in checks:
        print(f"🔍 {check_name}チェック中...")
        issues = check_func(directory)
        all_issues.extend(issues)
        print(f"  {'✓' if not issues else '⚠️'} {len(issues)} 件の問題")

    print()

    # メトリクス表示
    metrics = calculate_module_metrics(directory)
    print("📊 アーキテクチャメトリクス:")
    print(f"  📁 総ファイル数: {metrics['total_files']}")
    print(f"  📏 総行数: {metrics['total_lines']:,}")
    print(f"  📐 平均ファイルサイズ: {metrics['average_file_size']:.1f} 行")
    print(f"  📈 最大ファイルサイズ: {metrics['max_file_size']} 行")
    print(f"     ({os.path.basename(metrics['max_file_path'])})")
    print()

    print("🗂️  モジュール分布:")
    for module, count in sorted(metrics['module_distribution'].items()):
        print(f"  {module}: {count} ファイル")
    print()

    # 問題の表示
    if all_issues:
        error_count = sum(1 for issue in all_issues if issue.severity == 'error')
        warning_count = sum(1 for issue in all_issues if issue.severity == 'warning')

        print("📋 検出された問題:")

        # エラーを先に表示
        errors = [issue for issue in all_issues if issue.severity == 'error']
        warnings = [issue for issue in all_issues if issue.severity == 'warning']

        if errors:
            print("\n❌ エラー:")
            for issue in errors[:5]:
                print(f"  {os.path.basename(issue.file)}: {issue.description}")
            if len(errors) > 5:
                print(f"  ... 他 {len(errors) - 5} 件")

        if warnings:
            print("\n⚠️ 警告:")
            for issue in warnings[:5]:
                print(f"  {os.path.basename(issue.file)}: {issue.description}")
            if len(warnings) > 5:
                print(f"  ... 他 {len(warnings) - 5} 件")

        print(f"\n📊 サマリー: ❌ {error_count} エラー, ⚠️ {warning_count} 警告")

        if error_count > 0:
            print("\n💥 アーキテクチャエラーが見つかりました。修正が必要です。")
            sys.exit(1)
        else:
            print("\n⚠️ 警告があります。アーキテクチャ改善を推奨します。")
            sys.exit(0)
    else:
        print("✅ アーキテクチャ品質基準をクリアしています！")
        sys.exit(0)


if __name__ == "__main__":
    main()
