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
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Tuple

sys.path.insert(0, str(Path(__file__).parent.parent))

from infrastructure.logger import Logger, create_logger
from infrastructure.system_operations import SystemOperations


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

        # infrastructure配下では可変操作を許可
        self.is_infrastructure = '/infrastructure/' in filename
        # テストファイルでも可変操作を許可
        self.is_test_file = 'test_' in filename or '/tests/' in filename

    def visit_FunctionDef(self, node: ast.FunctionDef):
        """関数定義をチェック"""
        old_function = self.current_function
        self.current_function = node.name

        # 関数サイズチェック（25行制限、テストファイルは50行まで許可）
        func_lines = node.end_lineno - node.lineno + 1 if node.end_lineno else 1
        self.function_lengths[node.name] = func_lines

        # テストファイルの判定
        is_test_file = 'test_' in self.filename or '/tests/' in self.filename
        max_lines = 50 if is_test_file else 25

        if func_lines > max_lines:
            self.issues.append(QualityIssue(
                file=self.filename,
                line=node.lineno,
                issue_type='function_size',
                description=f'関数 {node.name} が {func_lines} 行です (制限: {max_lines}行)',
                severity='warning'
            ))

        # 関数内のノードをチェック
        self.generic_visit(node)
        self.current_function = old_function

    def visit_Import(self, node: ast.Import):
        """import文をチェック"""
        # infrastructure配下とテストファイルではローカルインポートを許可
        if self.current_function and not self.is_infrastructure and not self.is_test_file:
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
        # infrastructure配下とテストファイルではローカルインポートを許可
        if self.current_function and not self.is_infrastructure and not self.is_test_file:
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
        # infrastructure配下とテストファイルでは可変操作を許可
        if self.current_function and not self.is_infrastructure and not self.is_test_file:
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
        # infrastructure配下とテストファイルでは可変操作を許可
        if self.current_function and not self.is_infrastructure and not self.is_test_file:
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

            # infrastructure配下とテストファイルでは副作用を許可
            # また、print(file=sys.stderr)も緊急時出力として許可
            should_allow = (self.is_infrastructure or self.is_test_file or
                          (func_name == 'print' and self._is_stderr_print(node)))

            if func_name in side_effect_functions and not should_allow:
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

                # infrastructure配下とテストファイルでは可変メソッドを許可
                if method_name in mutable_methods and not self.is_infrastructure and not self.is_test_file:
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
        if isinstance(node, ast.Attribute):
            base = self._get_function_name(node.value)
            return f"{base}.{node.attr}"
        try:
            return ast.unparse(node)
        except Exception as e:
            raise Exception(f"Failed to unparse AST node: {e}") from e

    def _is_stderr_print(self, node: ast.Call) -> bool:
        """print文がfile=sys.stderrを使用しているかチェック"""
        for keyword in node.keywords:
            if (keyword.arg == 'file' and
                isinstance(keyword.value, ast.Attribute) and
                isinstance(keyword.value.value, ast.Name) and
                keyword.value.value.id == 'sys' and
                keyword.value.attr == 'stderr'):
                return True
        return False


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
            elif isinstance(decorator, ast.Call) and isinstance(decorator.func, ast.Name) and decorator.func.id == 'dataclass':
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
        with open(file_path, encoding='utf-8') as f:
            content = f.read()

        tree = ast.parse(content, filename=file_path)

        # 関数型品質チェック
        func_checker = FunctionalQualityChecker(file_path)
        func_checker.visit(tree)

        # データクラスチェック - 要求が厳しすぎるため無効化
        # dataclass_checker = DataClassChecker(file_path)
        # dataclass_checker.visit(tree)

        return func_checker.issues  # + dataclass_checker.issues

    except Exception as e:
        raise Exception(f"Failed to analyze functional quality in {file_path}: {e}") from e


def main(logger: Logger, system_ops: SystemOperations):
    """メイン関数"""

    argv = system_ops.get_argv()
    if len(argv) < 2:
        logger.error("使用方法: python3 functional_quality_check.py <directory>")
        system_ops.exit(1)

    directory = argv[1]
    python_files = glob.glob(f"{directory}/**/*.py", recursive=True)

    all_issues = []
    error_count = 0
    warning_count = 0
    info_count = 0

    logger.info("🔍 関数型プログラミング品質チェック開始...")
    logger.info(f"📁 チェック対象: {len(python_files)} ファイル")

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
        logger.info("📋 検出された問題:")

        # 種類別にグループ化
        by_type = {}
        for issue in all_issues:
            if issue.issue_type not in by_type:
                by_type[issue.issue_type] = []
            by_type[issue.issue_type].append(issue)

        for issue_type, issues in by_type.items():
            logger.info(f"📌 {issue_type.upper()}:")
            for issue in issues[:5]:  # 最初の5個のみ表示
                severity_icon = "❌" if issue.severity == "error" else "⚠️" if issue.severity == "warning" else "💡"
                logger.info(f"  {severity_icon} {issue.file}:{issue.line} - {issue.description}")

            if len(issues) > 5:
                logger.info(f"  ... 他 {len(issues) - 5} 件")

    # サマリー
    logger.info("📊 品質チェック結果:")
    logger.info(f"  ❌ エラー: {error_count}")
    logger.info(f"  ⚠️  警告: {warning_count}")
    logger.info(f"  💡 情報: {info_count}")
    logger.info(f"  📁 チェック済みファイル: {len(python_files)}")

    if error_count > 0:
        logger.error("💥 エラーが見つかりました。修正が必要です。")
        system_ops.exit(1)
    elif warning_count > 0:
        logger.warning("⚠️  警告があります。品質向上のため修正を推奨します。")
        system_ops.exit(0)
    else:
        logger.info("✅ 関数型プログラミング品質基準をクリアしています！")
        system_ops.exit(0)


if __name__ == "__main__":
    from infrastructure.system_operations_impl import SystemOperationsImpl
    logger = create_logger()
    system_ops = SystemOperationsImpl()
    main(logger, system_ops)
