"""テスト用ルール"""
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))
from models.check_result import CheckResult, FailureLocation

def main() -> CheckResult:
    """テスト用のチェックルール"""
    
    return CheckResult(
        failure_locations=[
            FailureLocation(file_path="src/test.py", line_number=10),
            FailureLocation(file_path="src/test2.py", line_number=20)
        ],
        fix_policy="これはテストです",
        fix_example_code="# テスト例"
    )

if __name__ == "__main__":
    result = main()
    print(f"テスト結果: {len(result.failure_locations)}件の問題")