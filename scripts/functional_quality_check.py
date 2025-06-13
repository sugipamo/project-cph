#!/usr/bin/env python3
"""
関数型プログラミング品質チェッカー

リファクタリング完了後の品質基準をチェックします：
- 純粋関数の原則遵守
- 関数サイズ制限
- 不変データ構造の使用
- 副作用の適切な分離
- ローカルインポートの禁止
"""

import ast
import glob
import sys
from pathlib import Path
from typing import List, Dict, Set, Tuple
from dataclasses import dataclass


@dataclass(frozen=True)
class QualityIssue:
    """品質問題を表現する不変データ構造"""
    file: str
    line: int
    issue_type: str
    description: str
    severity: str  # 'error', 'warning', 'info'


class FunctionalQualityChecker(ast.NodeVisitor):
    """関数型プログラミング品質をチェックするASTビジター"""
    
    def __init__(self, filename: str):
        self.filename = filename
        self.issues: List[QualityIssue] = []
        self.current_function = None
        self.function_lengths: Dict[str, int] = {}
        self.imports_in_functions: List[Tuple[str, int]] = []
        self.global_vars_usage: List[Tuple[str, int]] = []
        self.mutable_operations: List[Tuple[str, int]] = []
        
    def visit_FunctionDef(self, node: ast.FunctionDef):
        """関数定義をチェック"""
        old_function = self.current_function
        self.current_function = node.name
        
        # 関数サイズチェック（15行制限）
        func_lines = node.end_lineno - node.lineno + 1 if node.end_lineno else 1
        self.function_lengths[node.name] = func_lines
        
        if func_lines > 15:
            self.issues.append(QualityIssue(
                file=self.filename,
                line=node.lineno,
                issue_type='function_size',
                description=f'関数 {node.name} が {func_lines} 行です (制限: 15行)',
                severity='warning'
            ))
        
        # 関数内のノードをチェック
        self.generic_visit(node)
        self.current_function = old_function
    
    def visit_Import(self, node: ast.Import):
        """import文をチェック"""
        if self.current_function:
            self.imports_in_functions.append((self.current_function, node.lineno))
            self.issues.append(QualityIssue(
                file=self.filename,
                line=node.lineno,
                issue_type='local_import',
                description=f'関数 {self.current_function} 内でimportが使用されています',
                severity='error'
            ))
    
    def visit_ImportFrom(self, node: ast.ImportFrom):
        """from import文をチェック"""
        if self.current_function:
            self.imports_in_functions.append((self.current_function, node.lineno))
            self.issues.append(QualityIssue(
                file=self.filename,
                line=node.lineno,
                issue_type='local_import',
                description=f'関数 {self.current_function} 内でfrom importが使用されています',
                severity='error'
            ))
    
    def visit_Global(self, node: ast.Global):
        """global文をチェック（純粋関数違反）"""
        if self.current_function:
            for name in node.names:
                self.global_vars_usage.append((name, node.lineno))
                self.issues.append(QualityIssue(
                    file=self.filename,
                    line=node.lineno,
                    issue_type='global_usage',
                    description=f'関数 {self.current_function} でglobal変数 {name} を使用（純粋関数違反）',
                    severity='error'
                ))
    
    def visit_Assign(self, node: ast.Assign):
        """代入をチェック（可変操作の検出）"""
        if self.current_function:
            # リストの要素変更 (list[0] = value)
            for target in node.targets:
                if isinstance(target, ast.Subscript):
                    self.mutable_operations.append((ast.unparse(target), node.lineno))
                    self.issues.append(QualityIssue(
                        file=self.filename,
                        line=node.lineno,
                        issue_type='mutable_operation',
                        description=f'可変操作: {ast.unparse(target)} = ... (不変性違反)',
                        severity='warning'
                    ))
        self.generic_visit(node)
    
    def visit_AugAssign(self, node: ast.AugAssign):
        """拡張代入をチェック（+=, -=など）"""
        if self.current_function:
            self.mutable_operations.append((ast.unparse(node.target), node.lineno))
            self.issues.append(QualityIssue(
                file=self.filename,
                line=node.lineno,
                issue_type='mutable_operation',
                description=f'可変操作: {ast.unparse(node.target)} {ast.unparse(node.op)}= ... (不変性違反)',
                severity='warning'
            ))
        self.generic_visit(node)
    
    def visit_Call(self, node: ast.Call):
        """関数呼び出しをチェック（副作用検出）"""
        if self.current_function:
            func_name = self._get_function_name(node.func)
            
            # 副作用を持つ関数の検出
            side_effect_functions = {
                'print', 'input', 'open', 'write', 'mkdir', 'rmdir',
                'remove', 'rename', 'chmod', 'chown', 'system',
                'subprocess.run', 'subprocess.call', 'subprocess.Popen'
            }
            
            if func_name in side_effect_functions:
                self.issues.append(QualityIssue(
                    file=self.filename,
                    line=node.lineno,
                    issue_type='side_effect',
                    description=f'副作用関数 {func_name} の呼び出し（純粋関数違反）',
                    severity='warning'
                ))
            
            # list.append, dict.update などの可変メソッド
            if isinstance(node.func, ast.Attribute):
                method_name = node.func.attr
                mutable_methods = {
                    'append', 'extend', 'insert', 'remove', 'pop', 'clear',
                    'sort', 'reverse', 'update', 'setdefault', 'popitem'
                }
                
                if method_name in mutable_methods:
                    self.issues.append(QualityIssue(
                        file=self.filename,
                        line=node.lineno,
                        issue_type='mutable_method',
                        description=f'可変メソッド {method_name} の使用（不変性違反）',
                        severity='warning'
                    ))
        
        self.generic_visit(node)
    
    def _get_function_name(self, node: ast.AST) -> str:
        """関数名を取得"""
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            base = self._get_function_name(node.value)
            return f"{base}.{node.attr}"
        else:
            try:
                return ast.unparse(node)
            except:
                return "unknown"


class DataClassChecker(ast.NodeVisitor):
    """@dataclass(frozen=True) の使用をチェック"""
    
    def __init__(self, filename: str):
        self.filename = filename
        self.issues: List[QualityIssue] = []
    
    def visit_ClassDef(self, node: ast.ClassDef):
        """クラス定義をチェック"""
        has_dataclass = False
        has_frozen = False
        
        for decorator in node.decorator_list:
            if isinstance(decorator, ast.Name) and decorator.id == 'dataclass':
                has_dataclass = True
            elif isinstance(decorator, ast.Call):
                if isinstance(decorator.func, ast.Name) and decorator.func.id == 'dataclass':
                    has_dataclass = True
                    # frozen=True をチェック
                    for keyword in decorator.keywords:
                        if keyword.arg == 'frozen' and isinstance(keyword.value, ast.Constant) and keyword.value.value is True:
                            has_frozen = True
        
        # データクラスの場合、frozen=True をチェック
        if has_dataclass and not has_frozen:
            self.issues.append(QualityIssue(
                file=self.filename,
                line=node.lineno,
                issue_type='mutable_dataclass',
                description=f'@dataclass({node.name}) に frozen=True が指定されていません（不変性違反）',
                severity='warning'
            ))
        
        # 通常のクラスで __init__ がある場合の警告
        if not has_dataclass:
            for item in node.body:
                if isinstance(item, ast.FunctionDef) and item.name == '__init__':
                    self.issues.append(QualityIssue(
                        file=self.filename,
                        line=node.lineno,
                        issue_type='non_dataclass',
                        description=f'クラス {node.name} は @dataclass(frozen=True) の使用を検討してください',
                        severity='info'
                    ))
                    break
        
        self.generic_visit(node)


def check_file(file_path: str) -> List[QualityIssue]:
    """ファイルをチェックして問題を返す"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        tree = ast.parse(content, filename=file_path)
        
        # 関数型品質チェック
        func_checker = FunctionalQualityChecker(file_path)
        func_checker.visit(tree)
        
        # データクラスチェック
        dataclass_checker = DataClassChecker(file_path)
        dataclass_checker.visit(tree)
        
        return func_checker.issues + dataclass_checker.issues
        
    except Exception as e:
        return [QualityIssue(
            file=file_path,
            line=0,
            issue_type='parse_error',
            description=f'ファイル解析エラー: {e}',
            severity='error'
        )]


def main():
    """メイン関数"""
    if len(sys.argv) < 2:
        print("使用方法: python3 functional_quality_check.py <directory>")
        sys.exit(1)
    
    directory = sys.argv[1]
    python_files = glob.glob(f"{directory}/**/*.py", recursive=True)
    
    all_issues = []
    error_count = 0
    warning_count = 0
    info_count = 0
    
    print("🔍 関数型プログラミング品質チェック開始...")
    print(f"📁 チェック対象: {len(python_files)} ファイル")
    print()
    
    for file_path in python_files:
        issues = check_file(file_path)
        all_issues.extend(issues)
        
        for issue in issues:
            if issue.severity == 'error':
                error_count += 1
            elif issue.severity == 'warning':
                warning_count += 1
            else:
                info_count += 1
    
    # 結果表示
    if all_issues:
        print("📋 検出された問題:")
        print()
        
        # 種類別にグループ化
        by_type = {}
        for issue in all_issues:
            if issue.issue_type not in by_type:
                by_type[issue.issue_type] = []
            by_type[issue.issue_type].append(issue)
        
        for issue_type, issues in by_type.items():
            print(f"📌 {issue_type.upper()}:")
            for issue in issues[:5]:  # 最初の5個のみ表示
                severity_icon = "❌" if issue.severity == "error" else "⚠️" if issue.severity == "warning" else "💡"
                print(f"  {severity_icon} {issue.file}:{issue.line} - {issue.description}")
            
            if len(issues) > 5:
                print(f"  ... 他 {len(issues) - 5} 件")
            print()
    
    # サマリー
    print("📊 品質チェック結果:")
    print(f"  ❌ エラー: {error_count}")
    print(f"  ⚠️  警告: {warning_count}")
    print(f"  💡 情報: {info_count}")
    print(f"  📁 チェック済みファイル: {len(python_files)}")
    
    if error_count > 0:
        print()
        print("💥 エラーが見つかりました。修正が必要です。")
        sys.exit(1)
    elif warning_count > 0:
        print()
        print("⚠️  警告があります。品質向上のため修正を推奨します。")
        sys.exit(0)
    else:
        print()
        print("✅ 関数型プログラミング品質基準をクリアしています！")
        sys.exit(0)


if __name__ == "__main__":
    main()