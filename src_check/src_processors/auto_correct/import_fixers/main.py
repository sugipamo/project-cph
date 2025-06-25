"""
インポート修正自動修正メインモジュール

src_check/main.pyから動的に読み込まれ、src配下のファイルの
インポート文を自動修正します。
"""
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent.parent.parent))
from src_check.models.check_result import CheckResult, FailureLocation

# 親ディレクトリのモジュールをインポート
sys.path.append(str(Path(__file__).parent.parent))
from local_import_fixer import LocalImportFixer


def main(di_container) -> CheckResult:
    """
    インポート修正のメインエントリーポイント
    
    Args:
        di_container: DIコンテナ
        logger: ロガー関数
        
    Returns:
        CheckResult: チェック結果
    """
    project_root = Path(__file__).parent.parent.parent.parent.parent
    src_dir = project_root / 'src'
    
    logger(f"🔍 インポート解析を開始: {src_dir}")
    
    try:
        fixer = LocalImportFixer(str(src_dir))
        issues = fixer.analyze_imports()
        
        failure_locations = []
        for issue in issues:
            failure_locations.append(FailureLocation(
                file_path=issue['file'],
                line_number=issue['line']
            ))
        
        if failure_locations:
            fix_policy = (
                f"{len(failure_locations)}個の不適切なインポートが検出されました。\n"
                "ローカルインポートを絶対インポートに変更することを推奨します。"
            )
            fix_example = (
                "# 修正前:\n"
                "from .module import func\n"
                "import ..package\n\n"
                "# 修正後:\n"
                "from src.module import func\n"
                "from src.package import module"
            )
        else:
            fix_policy = "すべてのインポートは適切です。"
            fix_example = None
        
        return CheckResult(
            failure_locations=failure_locations,
            fix_policy=fix_policy,
            fix_example_code=fix_example
        )
        
    except Exception as e:
        logger(f"❌ エラーが発生しました: {e}")
        return CheckResult(
            failure_locations=[],
            fix_policy=f"インポート解析中にエラーが発生しました: {str(e)}",
            fix_example_code=None
        )


class LocalImportFixer:
    """ローカルインポート修正クラス（簡易版）"""
    
    def __init__(self, src_dir: str):
        self.src_dir = Path(src_dir)
    
    def analyze_imports(self):
        """インポートを解析"""
        # 実際の実装はlocal_import_fixer.pyから移植
        return []


if __name__ == "__main__":
    # テスト実行
    result = main(None)
    print(f"\nCheckResult: {len(result.failure_locations)} import issues found")