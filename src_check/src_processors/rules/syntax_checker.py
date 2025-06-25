"""
構文エラーチェックルール

Pythonファイルの構文エラーを検出します。
"""
import ast
from pathlib import Path
from typing import List
import sys
sys.path.append(str(Path(__file__).parent.parent))
from models.check_result import CheckResult, FailureLocation

def check_file(file_path: Path) -> List[FailureLocation]:
    """
    単一ファイルの構文をチェックする
    
    Args:
        file_path: チェック対象のファイルパス
    
    Returns:
        違反箇所のリスト
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        ast.parse(content, filename=str(file_path))
        return []
    except SyntaxError as e:
        return [FailureLocation(file_path=str(file_path), line_number=e.lineno or 0)]
    except Exception:
        return []

def main(di_container) -> CheckResult:
    """
    メインエントリーポイント
    
    Returns:
        CheckResult: チェック結果
    """
    project_root = Path(__file__).parent.parent.parent
    all_violations = []
    check_dirs = [project_root / 'src', project_root / 'tests', project_root / 'scripts']
    for check_dir in check_dirs:
        if check_dir.exists():
            for py_file in check_dir.rglob('*.py'):
                if '__pycache__' in str(py_file):
                    continue
                violations = check_file(py_file)
                all_violations.extend(violations)
    fix_policy = '構文エラーは即座に修正が必要です。IDEの構文チェック機能を活用してください。インデント、括弧の対応、コロンの抜けなどを確認してください。'
    fix_example = '# Before - 構文エラーの例\ndef process_data(data)  # コロンが抜けている\n    return data\n\n# After - 修正後\ndef process_data(data):  # コロンを追加\n    return data'
    return CheckResult(failure_locations=all_violations, fix_policy=fix_policy, fix_example_code=fix_example)
if __name__ == '__main__':
    result = main()
    logger(f'構文チェッカー: {len(result.failure_locations)}件の違反を検出')