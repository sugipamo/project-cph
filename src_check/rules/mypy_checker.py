"""
mypy静的型チェッカー

プロジェクト全体のPythonコードに対してmypyを実行し、
型エラーを検出します。
"""

import subprocess
import re
from pathlib import Path
from typing import List, Tuple
import sys

sys.path.append(str(Path(__file__).parent.parent))

from models.check_result import CheckResult, FailureLocation


def parse_mypy_output(output: str, project_root: Path) -> List[FailureLocation]:
    """
    mypyの出力を解析してFailureLocationリストに変換
    
    Args:
        output: mypyの実行結果
        project_root: プロジェクトルートパス
    
    Returns:
        違反箇所のリスト
    """
    violations = []
    
    # mypyの出力形式: path/to/file.py:行番号: エラー: メッセージ
    pattern = r'^(.+\.py):(\d+):\s*(?:error|note):\s*(.+)$'
    
    for line in output.strip().split('\n'):
        match = re.match(pattern, line)
        if match:
            file_path = match.group(1)
            line_number = int(match.group(2))
            
            # 相対パスを絶対パスに変換
            if not Path(file_path).is_absolute():
                file_path = str(project_root / file_path)
            
            # src/配下のファイルのみを対象とする
            if "/src/" in file_path:
                violations.append(FailureLocation(
                    file_path=file_path,
                    line_number=line_number
                ))
    
    return violations


def run_mypy(target_dir: Path) -> Tuple[List[FailureLocation], bool]:
    """
    指定ディレクトリに対してmypyを実行
    
    Args:
        target_dir: チェック対象のディレクトリ
    
    Returns:
        (違反箇所のリスト, mypyが正常に実行されたか)
    """
    project_root = target_dir.parent
    
    try:
        # mypyコマンドを実行
        # --no-error-summary: エラーサマリーを表示しない
        # --show-error-codes: エラーコードを表示
        # --ignore-missing-imports: 不足しているインポートを無視
        result = subprocess.run(
            ["python3", "-m", "mypy", str(target_dir), "--no-error-summary", "--show-error-codes", "--ignore-missing-imports", "--explicit-package-bases"],
            capture_output=True,
            text=True,
            cwd=str(project_root)
        )
        
        # mypyはエラーがある場合にexitcode 1を返すが、これは正常動作
        if result.returncode in [0, 1]:
            violations = parse_mypy_output(result.stdout, project_root)
            return violations, True
        else:
            # その他のエラー（mypyが見つからない等）
            print(f"mypyの実行に失敗しました: {result.stderr}")
            return [], False
            
    except FileNotFoundError:
        print("エラー: mypyがインストールされていません。'pip install mypy'を実行してください。")
        return [], False
    except Exception as e:
        print(f"mypyの実行中にエラーが発生しました: {e}")
        return [], False


def main() -> CheckResult:
    """
    メインエントリーポイント
    
    Returns:
        CheckResult: チェック結果
    """
    # プロジェクトルートを取得
    project_root = Path(__file__).parent.parent.parent
    src_dir = project_root / "src"
    
    if not src_dir.exists():
        return CheckResult(
            failure_locations=[],
            fix_policy="src/ディレクトリが見つかりません",
            fix_example_code=""
        )
    
    # mypyを実行
    violations, success = run_mypy(src_dir)
    
    if not success:
        return CheckResult(
            failure_locations=[],
            fix_policy="mypyの実行に失敗しました。mypyがインストールされているか確認してください。",
            fix_example_code="pip install mypy"
        )
    
    # 修正方針
    fix_policy = """型アノテーションを追加し、型エラーを修正してください。
以下の方法で対処できます：
1. 関数の引数と戻り値に型アノテーションを追加
2. 変数の型が曖昧な場合は型アノテーションを追加
3. Optional型やUnion型を適切に使用
4. 型の不一致がある場合は、適切な型変換を行う"""
    
    # 修正例
    fix_example = """# Before - 型アノテーションなし
def calculate_total(items):
    total = 0
    for item in items:
        total += item.price
    return total

# After - 型アノテーションあり
from typing import List

class Item:
    price: float

def calculate_total(items: List[Item]) -> float:
    total: float = 0
    for item in items:
        total += item.price
    return total

# Optional型の使用例
from typing import Optional

def find_user(user_id: int) -> Optional[User]:
    user = database.get_user(user_id)
    return user  # Noneかもしれない

# 使用時のNoneチェック
user = find_user(123)
if user is not None:
    print(user.name)"""
    
    return CheckResult(
        failure_locations=violations,
        fix_policy=fix_policy,
        fix_example_code=fix_example
    )


if __name__ == "__main__":
    # 直接実行時のテスト用
    result = main()
    print(f"mypyチェッカー: {len(result.failure_locations)}件の型エラーを検出")
    
    if result.failure_locations:
        print("\n違反箇所:")
        for location in result.failure_locations[:5]:
            print(f"  - {location.file_path}:{location.line_number}")
        
        if len(result.failure_locations) > 5:
            print(f"  ... 他 {len(result.failure_locations) - 5} 件")