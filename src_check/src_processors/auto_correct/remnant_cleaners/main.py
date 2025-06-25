"""
残骸フォルダ削除自動修正メインモジュール

src_check/main.pyから動的に読み込まれ、src配下の残骸フォルダを
自動削除します。残骸フォルダとは__pycache__および__init__.pyしか
入っていないフォルダです。
"""
import sys
from pathlib import Path
from typing import List, Set

sys.path.append(str(Path(__file__).parent.parent.parent.parent))
from src_check.models.check_result import CheckResult, FailureLocation


def main() -> CheckResult:
    """
    残骸フォルダ削除のメインエントリーポイント
        
    Returns:
        CheckResult: チェック結果
    """
    project_root = Path(__file__).parent.parent.parent.parent.parent
    src_dir = project_root / 'src'
    
    print(f"🔍 残骸フォルダ解析を開始: {src_dir}")
    
    try:
        remnant_cleaner = RemnantCleaner(str(src_dir))
        remnant_folders = remnant_cleaner.find_remnant_folders()
        
        failure_locations = []
        for folder_path in remnant_folders:
            failure_locations.append(FailureLocation(
                file_path=str(folder_path),
                line_number=0
            ))
        
        if failure_locations:
            fix_policy = (
                f"{len(failure_locations)}個の残骸フォルダが検出されました。\n"
                "__pycache__および__init__.pyのみが存在するフォルダを削除します。"
            )
            fix_example = (
                "# 削除対象フォルダの例:\n"
                "src/empty_module/  # __init__.pyのみ\n"
                "src/utils/__pycache__/  # __pycache__のみ\n"
                "src/old_package/  # __init__.pyと__pycache__のみ"
            )
        else:
            fix_policy = "残骸フォルダは見つかりませんでした。"
            fix_example = None
        
        return CheckResult(
            failure_locations=failure_locations,
            fix_policy=fix_policy,
            fix_example_code=fix_example
        )
        
    except Exception as e:
        print(f"❌ エラーが発生しました: {e}")
        return CheckResult(
            failure_locations=[],
            fix_policy=f"残骸フォルダ解析中にエラーが発生しました: {str(e)}",
            fix_example_code=None
        )


class RemnantCleaner:
    """残骸フォルダ検出・削除クラス"""
    
    def __init__(self, src_dir: str):
        self.src_dir = Path(src_dir)
    
    def find_remnant_folders(self) -> List[Path]:
        """残骸フォルダを検出する"""
        remnant_folders = []
        
        if not self.src_dir.exists():
            return remnant_folders
        
        for folder in self._get_all_directories():
            if self._is_remnant_folder(folder):
                remnant_folders.append(folder)
        
        return remnant_folders
    
    def _get_all_directories(self) -> List[Path]:
        """すべてのディレクトリを取得"""
        directories = []
        for item in self.src_dir.rglob('*'):
            if item.is_dir():
                directories.append(item)
        return directories
    
    def _is_remnant_folder(self, folder_path: Path) -> bool:
        """フォルダが残骸フォルダかどうかを判定"""
        if not folder_path.is_dir():
            return False
        
        # フォルダ内のファイル・ディレクトリを取得
        contents = list(folder_path.iterdir())
        
        if not contents:
            # 空のフォルダは残骸
            return True
        
        # 許可されるファイル・ディレクトリ名のセット
        allowed_items = {'__init__.py', '__pycache__'}
        
        # すべてのアイテムが許可リストに含まれているかチェック
        for item in contents:
            if item.name not in allowed_items:
                return False
        
        # __init__.pyが存在する場合、空でないかチェック
        init_file = folder_path / '__init__.py'
        if init_file.exists():
            if self._is_meaningful_init_file(init_file):
                return False
        
        return True
    
    def _is_meaningful_init_file(self, init_file: Path) -> bool:
        """__init__.pyが意味のあるコンテンツを持っているかチェック"""
        try:
            content = init_file.read_text(encoding='utf-8').strip()
            
            # 空ファイルまたはコメントのみの場合は意味がない
            if not content:
                return False
            
            # コメント行のみかチェック
            lines = content.split('\n')
            meaningful_lines = []
            for line in lines:
                stripped = line.strip()
                if stripped and not stripped.startswith('#'):
                    meaningful_lines.append(stripped)
            
            # 意味のある行がない場合は残骸
            return len(meaningful_lines) > 0
            
        except Exception:
            # 読み取りエラーの場合は保守的に意味があると判定
            return True
    
    def clean_remnant_folders(self, dry_run: bool = True) -> List[Path]:
        """残骸フォルダを削除"""
        import shutil
        
        remnant_folders = self.find_remnant_folders()
        cleaned_folders = []
        
        for folder in remnant_folders:
            try:
                if not dry_run:
                    shutil.rmtree(folder)
                    print(f"削除しました: {folder}")
                else:
                    print(f"削除対象: {folder}")
                cleaned_folders.append(folder)
            except Exception as e:
                print(f"削除失敗: {folder} - {e}")
        
        return cleaned_folders


if __name__ == "__main__":
    # テスト実行
    result = main()
    print(f"\nCheckResult: {len(result.failure_locations)} remnant folders found")