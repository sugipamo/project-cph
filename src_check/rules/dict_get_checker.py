"""
dict.get()使用チェックルール

dict.get()の使用を検出します。
CLAUDE.mdルールに従い、デフォルト値の使用は禁止されています。
"""

import ast
from pathlib import Path
from typing import List

import sys
sys.path.append(str(Path(__file__).parent.parent))

from models.check_result import CheckResult, FailureLocation


class DictGetChecker(ast.NodeVisitor):
    """
    dict.get()の使用をチェックするクラス
    """
    
    def __init__(self, file_path: str):
        self.file_path = file_path
        self.violations = []
    
    def visit_Call(self, node):
        """メソッド呼び出しをチェック"""
        # dict.get()の呼び出しを検出
        if isinstance(node.func, ast.Attribute) and node.func.attr == 'get':
            # getメソッドが呼ばれている場合、違反として記録
            self.violations.append(FailureLocation(
                file_path=self.file_path,
                line_number=node.lineno
            ))
        
        self.generic_visit(node)


def check_file(file_path: Path) -> List[FailureLocation]:
    """
    単一ファイルのdict.get()使用をチェックする
    
    Args:
        file_path: チェック対象のファイルパス
    
    Returns:
        違反箇所のリスト
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        tree = ast.parse(content, filename=str(file_path))
        
        checker = DictGetChecker(str(file_path))
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
dict.get()の使用は禁止されています。
設定値は明示的に設定ファイル（{setting}.json）に定義してください。
src/configuration/readme.mdの設定取得方法に従ってください。
デフォルト値ではなく、適切な設定管理を実装してください。"""
    
    fix_example = """# Before - dict.get()の使用
config = load_config()
timeout = config.get('timeout', 30)  # デフォルト値を使用
retry_count = config.get('retry_count', 3)

# After - 明示的な設定管理
# 1. 設定ファイルに明示的に定義 (config.json)
{
    "timeout": 30,
    "retry_count": 3
}

# 2. ConfigManagerを使用して取得
from src.configuration.config_manager import ConfigManager

config_manager = ConfigManager(file_handler)
timeout = config_manager.get_value('timeout')  # 設定が存在しない場合はエラー
retry_count = config_manager.get_value('retry_count')

# 3. 存在チェックが必要な場合
if 'optional_setting' in config:
    value = config['optional_setting']
else:
    # デフォルト値ではなく、適切なエラーハンドリング
    raise ConfigurationError("optional_settingが設定されていません")"""
    
    return CheckResult(
        failure_locations=all_violations,
        fix_policy=fix_policy,
        fix_example_code=fix_example
    )


if __name__ == "__main__":
    result = main()
    print(f"dict.get()使用チェッカー: {len(result.failure_locations)}件の違反を検出")