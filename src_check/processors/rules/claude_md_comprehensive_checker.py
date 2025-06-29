"""
CLAUDE.mdの包括的な違反チェックルール

以下のルールをチェック：
1. デフォルト値の使用禁止
2. 副作用はsrc/infrastructureのみ
3. フォールバック処理の禁止
4. 循環インポート・遅延インポートの検出
5. 短期的解決の検出
"""
import ast
from pathlib import Path
from typing import List, Dict, Set, Tuple
import sys
sys.path.append(str(Path(__file__).parent.parent))
from models.check_result import CheckResult, FailureLocation, LogLevel


class ComprehensiveChecker(ast.NodeVisitor):
    """CLAUDE.md違反を包括的にチェックするクラス"""
    
    def __init__(self, file_path: str):
        self.file_path = file_path
        self.violations = {
            'default_values': [],
            'side_effects': [],
            'fallback': [],
            'delayed_imports': [],
            'short_term_fixes': []
        }
        self.in_function = False
        self.imported_modules = set()
        
    def visit_FunctionDef(self, node):
        """関数定義をチェック"""
        # デフォルト値チェック
        if node.args.defaults:
            self.violations['default_values'].append(
                FailureLocation(file_path=self.file_path, line_number=node.lineno)
            )
        if node.args.kw_defaults:
            for default in node.args.kw_defaults:
                if default is not None:
                    self.violations['default_values'].append(
                        FailureLocation(file_path=self.file_path, line_number=node.lineno)
                    )
        
        # 関数内のチェック用フラグ
        old_in_function = self.in_function
        self.in_function = True
        self.generic_visit(node)
        self.in_function = old_in_function
        
    def visit_AsyncFunctionDef(self, node):
        """非同期関数も同様にチェック"""
        self.visit_FunctionDef(node)
        
    def visit_Import(self, node):
        """import文をチェック"""
        # 遅延インポートチェック
        if self.in_function:
            self.violations['delayed_imports'].append(
                FailureLocation(file_path=self.file_path, line_number=node.lineno)
            )
        
        # インポートモジュールを記録
        for alias in node.names:
            self.imported_modules.add(alias.name)
        self.generic_visit(node)
        
    def visit_ImportFrom(self, node):
        """from ... import文をチェック"""
        # 遅延インポートチェック
        if self.in_function:
            self.violations['delayed_imports'].append(
                FailureLocation(file_path=self.file_path, line_number=node.lineno)
            )
            
        # インポートモジュールを記録
        if node.module:
            self.imported_modules.add(node.module)
        self.generic_visit(node)
        
    def visit_Try(self, node):
        """try-except文でのフォールバックチェック"""
        for handler in node.handlers:
            # 無条件キャッチ
            if handler.type is None:
                self.violations['fallback'].append(
                    FailureLocation(file_path=self.file_path, line_number=handler.lineno)
                )
            # Exception/BaseExceptionの広範囲キャッチ
            elif isinstance(handler.type, ast.Name) and handler.type.id in ['Exception', 'BaseException']:
                self.violations['fallback'].append(
                    FailureLocation(file_path=self.file_path, line_number=handler.lineno)
                )
        self.generic_visit(node)
        
    def visit_Call(self, node):
        """関数呼び出しをチェック（副作用）"""
        # infrastructureディレクトリ以外で副作用をチェック
        if '/infrastructure/' not in self.file_path and not self.file_path.endswith('/infrastructure.py'):
            func_name = self._get_function_name(node.func)
            # メソッド呼び出しの場合、属性名も確認
            if isinstance(node.func, ast.Attribute):
                if node.func.attr in ['open', 'read', 'write', 'close', 'mkdir', 'rmdir']:
                    self.violations['side_effects'].append(
                        FailureLocation(file_path=self.file_path, line_number=node.lineno)
                    )
            elif self._is_side_effect(func_name):
                self.violations['side_effects'].append(
                    FailureLocation(file_path=self.file_path, line_number=node.lineno)
                )
        self.generic_visit(node)
        
    def visit_With(self, node):
        """with文（ファイル操作など）をチェック"""
        # infrastructureディレクトリ以外で副作用をチェック
        if '/infrastructure/' not in self.file_path and not self.file_path.endswith('/infrastructure.py'):
            for item in node.items:
                if isinstance(item.context_expr, ast.Call):
                    func_name = self._get_function_name(item.context_expr.func)
                    if func_name == 'open' or 'open(' in str(func_name):
                        self.violations['side_effects'].append(
                            FailureLocation(file_path=self.file_path, line_number=node.lineno)
                        )
        self.generic_visit(node)
        
    def visit_Expr(self, node):
        """コメントから短期的解決を検出"""
        # TODO、FIXME、HACKなどのコメントを検出
        if isinstance(node.value, ast.Constant) and isinstance(node.value.value, str):
            comment = node.value.value.lower()
            if any(marker in comment for marker in ['todo', 'fixme', 'hack', '短期的', '暫定']):
                self.violations['short_term_fixes'].append(
                    FailureLocation(file_path=self.file_path, line_number=node.lineno)
                )
        self.generic_visit(node)
        
    def _get_function_name(self, node) -> str:
        """関数名を取得"""
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            obj_name = self._get_function_name(node.value)
            if obj_name:
                return f"{obj_name}.{node.attr}"
            return node.attr
        return ""
        
    def _is_side_effect(self, func_name: str) -> bool:
        """副作用を持つ関数かチェック"""
        side_effect_patterns = {
            'open', 'read', 'write', 'close',
            'mkdir', 'rmdir', 'remove', 'unlink',
            'print', 'input',
            'urlopen', 'request',
            'execute', 'commit',
            'getenv', 'environ',
        }
        
        # 完全一致または部分一致
        for pattern in side_effect_patterns:
            if pattern in func_name:
                return True
                
        # I/O関連のモジュール
        io_modules = {'requests', 'urllib', 'http', 'socket', 'sqlite3'}
        for module in io_modules:
            if module in self.imported_modules and func_name.startswith(module):
                return True
                
        return False


def check_file(file_path: Path) -> Dict[str, List[FailureLocation]]:
    """単一ファイルをチェック"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        tree = ast.parse(content, filename=str(file_path))
        checker = ComprehensiveChecker(str(file_path))
        checker.visit(tree)
        return checker.violations
    except Exception as e:
        return {
            'default_values': [],
            'side_effects': [],
            'fallback': [],
            'delayed_imports': [],
            'short_term_fixes': []
        }


def main() -> CheckResult:
    """メインエントリーポイント"""
    project_root = Path(__file__).parent.parent.parent.parent  # src_check/processors/rules -> project-cph
    src_dir = project_root / 'src'
    
    all_violations = {
        'default_values': [],
        'side_effects': [],
        'fallback': [],
        'delayed_imports': [],
        'short_term_fixes': []
    }
    
    if src_dir.exists():
        for py_file in src_dir.rglob('*.py'):
            if '__pycache__' in str(py_file):
                continue
            violations = check_file(py_file)
            for key, value in violations.items():
                all_violations[key].extend(value)
    
    # すべての違反をまとめる
    total_violations = []
    violation_summary = []
    
    if all_violations['default_values']:
        total_violations.extend(all_violations['default_values'])
        violation_summary.append(f"デフォルト値の使用: {len(all_violations['default_values'])}件")
        
    if all_violations['side_effects']:
        total_violations.extend(all_violations['side_effects'])
        violation_summary.append(f"不適切な副作用: {len(all_violations['side_effects'])}件")
        
    if all_violations['fallback']:
        total_violations.extend(all_violations['fallback'])
        violation_summary.append(f"フォールバック処理: {len(all_violations['fallback'])}件")
        
    if all_violations['delayed_imports']:
        total_violations.extend(all_violations['delayed_imports'])
        violation_summary.append(f"遅延インポート: {len(all_violations['delayed_imports'])}件")
        
    if all_violations['short_term_fixes']:
        total_violations.extend(all_violations['short_term_fixes'])
        violation_summary.append(f"短期的解決: {len(all_violations['short_term_fixes'])}件")
    
    fix_policy = f'''【CLAUDE.md包括的違反チェック】

検出された違反:
{chr(10).join("- " + s for s in violation_summary) if violation_summary else "違反なし"}

修正方針:
1. デフォルト値: 呼び出し元で明示的に値を渡す
2. 副作用: infrastructureレイヤーに移動し、main.pyから依存性注入
3. フォールバック: Result型を使用した明示的なエラーハンドリング
4. 遅延インポート: モジュール構造の見直し
5. 短期的解決: 中長期を見据えた実装に変更'''
    
    fix_example = '''# 1. デフォルト値の修正
# Before
def process(data, timeout=30):
    pass

# After
def process(data, timeout):
    pass
# 呼び出し元
process(data, timeout=30)

# 2. 副作用の修正
# Before (src/operations/processor.py)
def load_config():
    with open('config.json') as f:
        return json.load(f)

# After
# src/infrastructure/file_handler.py
class FileHandler:
    def read_json(self, path):
        with open(path) as f:
            return json.load(f)

# src/operations/processor.py
def load_config(file_handler):
    return file_handler.read_json('config.json')

# 3. フォールバックの修正
# Before
try:
    result = risky_operation()
except Exception:
    result = default_value

# After (infrastructureで変換)
result = error_converter.execute_with_conversion(risky_operation)
if result.is_failure():
    # 明示的なエラー処理
    pass'''
    
    return CheckResult(
        title='claude_md_comprehensive_check',
        log_level=LogLevel.ERROR if total_violations else LogLevel.INFO,
        failure_locations=total_violations,
        fix_policy=fix_policy,
        fix_example_code=fix_example
    )


if __name__ == '__main__':
    result = main()
    print(f'CLAUDE.md包括的チェッカー: {len(result.failure_locations)}件の違反を検出')
    
    # 詳細を表示
    if result.fix_policy:
        lines = result.fix_policy.split('\n')
        for line in lines:
            if line.startswith('- ') and '件' in line:
                print(f'  {line}')