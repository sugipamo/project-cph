"""
pytest実行チェッカー

すべてのテストをpytestで実行し、失敗したテストの情報を収集します。
"""

import ast
import subprocess
import sys
from pathlib import Path
from typing import List

sys.path.append(str(Path(__file__).parent.parent))

from models.check_result import CheckResult, FailureLocation


def run_pytest() -> tuple[List[FailureLocation], str]:
    """
    pytestを実行してテスト結果を取得
    
    Returns:
        (失敗箇所のリスト, 詳細な出力)
    """
    project_root = Path(__file__).parent.parent.parent
    
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pytest", "-v", "--tb=short", "--continue-on-collection-errors"],
            cwd=str(project_root),
            capture_output=True,
            text=True
        )
        
        failures = []
        output = result.stdout + result.stderr
        
        if result.returncode != 0:
            lines = output.split('\n')
            for i, line in enumerate(lines):
                # Handle both FAILED and ERROR cases
                if ("FAILED" in line or "ERROR" in line) and (".py" in line):
                    # Extract file path from various formats
                    if "::" in line:
                        # Format: tests/test_file.py::test_name FAILED
                        file_test = line.split("::")[0].strip()
                    elif "ERROR" in line:
                        # Format: ERROR tests/test_file.py
                        parts = line.split()
                        file_test = None
                        for part in parts:
                            if part.endswith(".py"):
                                file_test = part
                                break
                    else:
                        continue
                    
                    if file_test and file_test.endswith(".py"):
                        file_path = project_root / file_test
                        if file_path.exists():
                            failures.append(FailureLocation(
                                file_path=str(file_path),
                                line_number=1
                            ))
        
        return failures, output
        
    except Exception as e:
        return [], f"pytest実行エラー: {str(e)}"


def main() -> CheckResult:
    """
    メインエントリーポイント
    
    Returns:
        CheckResult: チェック結果
    """
    failures, output = run_pytest()
    
    fix_policy = """テストが失敗している場合は以下の対応を行ってください：
1. エラーメッセージを確認して失敗原因を特定
2. テストコードまたは実装コードを修正
3. すべてのテストが通るまで修正を繰り返す"""
    
    fix_example = """# テスト失敗例
def test_add():
    assert add(2, 3) == 6  # 期待値が間違っている

# 修正後
def test_add():
    assert add(2, 3) == 5  # 正しい期待値に修正

# または実装側の修正が必要な場合
def add(a, b):
    return a + b  # 正しい実装に修正"""
    
    return CheckResult(
        failure_locations=failures,
        fix_policy=fix_policy,
        fix_example_code=fix_example
    )


if __name__ == "__main__":
    result = main()
    print(f"pytestチェッカー: {len(result.failure_locations)}件のテスト失敗を検出")
    
    if result.failure_locations:
        print("\n失敗したテストファイル:")
        for location in result.failure_locations[:5]:
            print(f"  - {location.file_path}")
        
        if len(result.failure_locations) > 5:
            print(f"  ... 他 {len(result.failure_locations) - 5} 件")