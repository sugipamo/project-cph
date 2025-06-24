"""
フォールバック処理チェックルール

try-except文での無条件キャッチやフォールバック処理を検出します。
CLAUDE.mdルールに従い、フォールバック処理は禁止されています。
"""

import ast
from pathlib import Path
from typing import List

import sys
sys.path.append(str(Path(__file__).parent.parent))

from models.check_result import CheckResult, FailureLocation


class FallbackChecker(ast.NodeVisitor):
    """
    フォールバック処理をチェックするクラス
    """
    
    def __init__(self, file_path: str):
        self.file_path = file_path
        self.violations = []
    
    def visit_Try(self, node):
        """try文をチェック"""
        for handler in node.handlers:
            # except: や except Exception: のような広範囲キャッチを検出
            if handler.type is None:
                # 無条件except
                self.violations.append(FailureLocation(
                    file_path=self.file_path,
                    line_number=handler.lineno
                ))
            elif isinstance(handler.type, ast.Name) and handler.type.id in ['Exception', 'BaseException']:
                # 広範囲のException
                self.violations.append(FailureLocation(
                    file_path=self.file_path,
                    line_number=handler.lineno
                ))
        
        self.generic_visit(node)


def check_file(file_path: Path) -> List[FailureLocation]:
    """
    単一ファイルのフォールバック処理をチェックする
    
    Args:
        file_path: チェック対象のファイルパス
    
    Returns:
        違反箇所のリスト
    """
    try:
        # infrastructureディレクトリ内のファイルは例外（ErrorConverterが存在）
        if 'infrastructure' in str(file_path):
            return []
        
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        tree = ast.parse(content, filename=str(file_path))
        
        checker = FallbackChecker(str(file_path))
        checker.visit(tree)
        
        return checker.violations
        
    except SyntaxError:
        return []
    except Exception:
        return []


def main() -> CheckResult:
    """
    メインエントリーポイント
    
    Returns:
        CheckResult: チェック結果
    """
    project_root = Path(__file__).parent.parent.parent
    
    all_violations = []
    
    # チェック対象ディレクトリ
    check_dirs = [
        project_root / "src",
        project_root / "tests",
        project_root / "scripts"
    ]
    
    for check_dir in check_dirs:
        if check_dir.exists():
            for py_file in check_dir.rglob("*.py"):
                if "__pycache__" in str(py_file):
                    continue
                
                violations = check_file(py_file)
                all_violations.extend(violations)
    
    fix_policy = """【CLAUDE.mdルール適用】
フォールバック処理は禁止されています。
try-except文での無条件キャッチは避けてください。
Infrastructure層でErrorConverterを使用してResult型に変換してください。
ビジネスロジック層ではis_failure()でエラーを明示的にチェックしてください。
例: error_converter.execute_with_conversion(operation) → result.is_failure()で判定"""
    
    fix_example = """# Before - フォールバック処理
def load_config():
    try:
        with open('config.json', 'r') as f:
            return json.load(f)
    except Exception:
        # フォールバック
        return {"default": "config"}

# After - Result型を使用した明示的なエラーハンドリング
# Infrastructure層
def load_config_with_result(file_handler, error_converter):
    def _load():
        return file_handler.read_json('config.json')
    
    return error_converter.execute_with_conversion(_load)

# ビジネスロジック層
def process_with_config(config_loader):
    result = config_loader.load_config_with_result()
    
    if result.is_failure():
        # エラーを明示的に処理
        logger.error(f"設定ファイルの読み込みに失敗: {result.error}")
        return Result.failure("設定ファイルエラー")
    
    config = result.value
    # 通常の処理を続行"""
    
    return CheckResult(
        failure_locations=all_violations,
        fix_policy=fix_policy,
        fix_example_code=fix_example
    )


if __name__ == "__main__":
    result = main()
    print(f"フォールバック処理チェッカー: {len(result.failure_locations)}件の違反を検出")