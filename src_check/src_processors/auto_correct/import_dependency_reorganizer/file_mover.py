"""
ファイル移動実行器
バックアップとロールバック機能付きの安全なファイル移動
"""

import shutil
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple, Optional
import subprocess

class FileMover:
    """
    ファイル移動を実行し、バックアップとロールバック機能を提供
    """
    
    def __init__(self, src_root: Path, use_git: bool = True):
        self.src_root = src_root
        self.use_git = use_git and self._is_git_repo()
        self.move_history: List[Dict] = []
        self.backup_dir = None
        
    def _is_git_repo(self) -> bool:
        """Gitリポジトリかどうかを確認"""
        try:
            result = subprocess.run(
                ["git", "rev-parse", "--git-dir"],
                cwd=self.src_root,
                capture_output=True,
                text=True
            )
            return result.returncode == 0
        except:
            return False
    
    def create_backup(self, move_plan: Dict[Path, Path]) -> Optional[Path]:
        """
        移動前のバックアップを作成
        Returns: バックアップディレクトリのパス
        """
        if self.use_git:
            # Gitでの変更確認
            result = subprocess.run(
                ["git", "status", "--porcelain"],
                cwd=self.src_root,
                capture_output=True,
                text=True
            )
            
            if result.stdout.strip():
                print("⚠️  警告: コミットされていない変更があります")
                print("移動を実行する前にコミットすることを推奨します")
                
            # 現在のコミットハッシュを記録
            result = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                cwd=self.src_root,
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                commit_hash = result.stdout.strip()
                print(f"📌 現在のコミット: {commit_hash}")
                return None  # Gitがバックアップとして機能
        
        # Git以外の場合はファイルコピーでバックアップ
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.backup_dir = self.src_root.parent / f"backup_reorganize_{timestamp}"
        self.backup_dir.mkdir(exist_ok=True)
        
        print(f"📦 バックアップを作成: {self.backup_dir}")
        
        for old_path in move_plan.keys():
            if old_path.exists():
                relative_path = old_path.relative_to(self.src_root)
                backup_path = self.backup_dir / relative_path
                backup_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(old_path, backup_path)
        
        # バックアップ情報を保存
        info = {
            "timestamp": timestamp,
            "move_plan": {str(k): str(v) for k, v in move_plan.items()},
            "file_count": len(move_plan)
        }
        
        with open(self.backup_dir / "backup_info.json", "w") as f:
            json.dump(info, f, indent=2)
        
        return self.backup_dir
    
    def execute_moves(self, move_plan: Dict[Path, Path], 
                     create_init_files: bool = True) -> Tuple[int, List[str]]:
        """
        ファイル移動を実行
        Returns: (成功数, エラーリスト)
        """
        success_count = 0
        errors = []
        
        print(f"\n🚀 ファイル移動を開始: {len(move_plan)}ファイル")
        
        # まず必要なディレクトリを作成
        directories_to_create = set()
        for new_path in move_plan.values():
            directories_to_create.add(new_path.parent)
        
        for directory in sorted(directories_to_create):
            if not directory.exists():
                directory.mkdir(parents=True, exist_ok=True)
                print(f"📁 ディレクトリ作成: {directory.relative_to(self.src_root)}")
                
                # __init__.pyファイルを作成
                if create_init_files:
                    init_file = directory / "__init__.py"
                    if not init_file.exists():
                        init_file.write_text("")
        
        # ファイルを移動
        for old_path, new_path in move_plan.items():
            try:
                if not old_path.exists():
                    errors.append(f"ファイルが存在しません: {old_path}")
                    continue
                
                # 移動先が既に存在する場合
                if new_path.exists():
                    errors.append(f"移動先が既に存在: {new_path}")
                    continue
                
                # ファイルを移動
                shutil.move(str(old_path), str(new_path))
                success_count += 1
                
                # 履歴に記録
                self.move_history.append({
                    "old": str(old_path),
                    "new": str(new_path),
                    "timestamp": datetime.now().isoformat()
                })
                
                # 進捗表示（10ファイルごと）
                if success_count % 10 == 0:
                    print(f"  ✓ {success_count}ファイル移動完了...")
                    
            except Exception as e:
                errors.append(f"{old_path}: {str(e)}")
        
        # 空のディレクトリを削除
        self._cleanup_empty_directories()
        
        print(f"\n✅ 移動完了: {success_count}/{len(move_plan)}ファイル")
        
        if errors:
            print(f"❌ エラー: {len(errors)}件")
            for error in errors[:5]:  # 最初の5件だけ表示
                print(f"  - {error}")
        
        return success_count, errors
    
    def _cleanup_empty_directories(self) -> None:
        """空のディレクトリを削除"""
        # src配下のすべてのディレクトリを深い順にチェック
        directories = []
        for path in self.src_root.rglob("*"):
            if path.is_dir():
                directories.append(path)
        
        # 深い順にソート（深いディレクトリから削除）
        directories.sort(key=lambda p: len(p.parts), reverse=True)
        
        removed_count = 0
        for directory in directories:
            try:
                # __pycache__は無視
                if directory.name == "__pycache__":
                    continue
                
                # 空のディレクトリ（__init__.pyのみも含む）を削除
                contents = list(directory.iterdir())
                if not contents or (len(contents) == 1 and contents[0].name == "__init__.py"):
                    if len(contents) == 1:
                        contents[0].unlink()  # __init__.pyを削除
                    directory.rmdir()
                    removed_count += 1
            except:
                pass  # エラーは無視
        
        if removed_count > 0:
            print(f"🧹 {removed_count}個の空ディレクトリを削除")
    
    def rollback(self) -> bool:
        """
        最後の移動操作をロールバック
        Returns: 成功フラグ
        """
        if self.use_git:
            print("📌 Gitを使用したロールバック")
            print("以下のコマンドで変更を元に戻せます:")
            print("  git checkout -- .")
            print("  git clean -fd")
            return True
        
        if not self.backup_dir or not self.backup_dir.exists():
            print("❌ バックアップが見つかりません")
            return False
        
        print(f"🔄 バックアップからロールバック: {self.backup_dir}")
        
        try:
            # バックアップ情報を読み込み
            with open(self.backup_dir / "backup_info.json") as f:
                info = json.load(f)
            
            # ファイルを元の場所に戻す
            restored_count = 0
            for old_path_str in info["move_plan"].keys():
                old_path = Path(old_path_str)
                relative_path = old_path.relative_to(self.src_root)
                backup_path = self.backup_dir / relative_path
                
                if backup_path.exists():
                    old_path.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(backup_path, old_path)
                    restored_count += 1
            
            print(f"✅ {restored_count}ファイルを復元しました")
            return True
            
        except Exception as e:
            print(f"❌ ロールバックエラー: {e}")
            return False
    
    def save_move_report(self, move_plan: Dict[Path, Path], 
                        success_count: int, errors: List[str]) -> Path:
        """移動レポートを保存"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = self.src_root.parent / f"reorganize_report_{timestamp}.json"
        
        report = {
            "timestamp": timestamp,
            "summary": {
                "total_files": len(move_plan),
                "success_count": success_count,
                "error_count": len(errors)
            },
            "move_plan": {str(k): str(v) for k, v in move_plan.items()},
            "errors": errors,
            "move_history": self.move_history
        }
        
        with open(report_file, "w") as f:
            json.dump(report, f, indent=2)
        
        print(f"\n📄 レポートを保存: {report_file}")
        return report_file


def test_file_mover():
    """ファイル移動器のテスト"""
    import tempfile
    
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        src_dir = tmp_path / "src"
        src_dir.mkdir()
        
        # テストファイルを作成
        (src_dir / "module1.py").write_text("# Module 1")
        (src_dir / "module2.py").write_text("# Module 2")
        
        # 移動計画
        move_plan = {
            src_dir / "module1.py": src_dir / "components" / "module1" / "module1.py",
            src_dir / "module2.py": src_dir / "services" / "module2" / "module2.py"
        }
        
        # ファイル移動を実行
        mover = FileMover(src_dir, use_git=False)
        backup_dir = mover.create_backup(move_plan)
        success_count, errors = mover.execute_moves(move_plan)
        
        print(f"\nテスト結果:")
        print(f"成功: {success_count}, エラー: {len(errors)}")
        
        # 移動先を確認
        assert (src_dir / "components" / "module1" / "module1.py").exists()
        assert (src_dir / "services" / "module2" / "module2.py").exists()
        
        # 元の場所にないことを確認
        assert not (src_dir / "module1.py").exists()
        assert not (src_dir / "module2.py").exists()


if __name__ == "__main__":
    test_file_mover()