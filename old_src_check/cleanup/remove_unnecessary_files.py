#!/usr/bin/env python3
"""
不要ファイル削除スクリプト

以下を削除対象とする：
1. __pycache__ディレクトリとその内容
2. コメントのみの__init__.pyファイル
3. 空のディレクトリ（深さ優先探索で削除）
"""

import os
import shutil
from pathlib import Path
from typing import List, Set
import ast


class UnnecessaryFileCleaner:
    """不要ファイル・フォルダを削除するクラス"""
    
    def __init__(self, target_dir: Path):
        self.target_dir = target_dir
        self.removed_files: List[Path] = []
        self.removed_dirs: List[Path] = []
        self.empty_init_files: List[Path] = []
    
    def clean(self):
        """メイン処理：不要ファイルとフォルダを削除"""
        print(f"🧹 クリーンアップ開始: {self.target_dir}")
        print("=" * 60)
        
        # 1. __pycache__ディレクトリを削除
        self._remove_pycache_dirs()
        
        # 2. コメントのみの__init__.pyを削除
        self._remove_empty_init_files()
        
        # 3. 空のディレクトリを削除（深さ優先）
        self._remove_empty_dirs()
        
        # 結果表示
        self._print_summary()
    
    def _remove_pycache_dirs(self):
        """__pycache__ディレクトリを再帰的に削除"""
        print("\n📁 __pycache__ディレクトリを検索中...")
        
        pycache_dirs = list(self.target_dir.rglob("__pycache__"))
        
        for pycache_dir in pycache_dirs:
            try:
                shutil.rmtree(pycache_dir)
                self.removed_dirs.append(pycache_dir)
                print(f"  ✓ 削除: {pycache_dir.relative_to(self.target_dir.parent)}")
            except Exception as e:
                print(f"  ✗ エラー: {pycache_dir} - {e}")
        
        if not pycache_dirs:
            print("  → __pycache__ディレクトリは見つかりませんでした")
    
    def _remove_empty_init_files(self):
        """コメントのみの__init__.pyファイルを削除"""
        print("\n📄 空の__init__.pyファイルを検索中...")
        
        init_files = list(self.target_dir.rglob("__init__.py"))
        
        for init_file in init_files:
            if self._is_empty_or_comment_only(init_file):
                try:
                    init_file.unlink()
                    self.empty_init_files.append(init_file)
                    print(f"  ✓ 削除: {init_file.relative_to(self.target_dir.parent)}")
                except Exception as e:
                    print(f"  ✗ エラー: {init_file} - {e}")
        
        if not self.empty_init_files:
            print("  → 空の__init__.pyファイルは見つかりませんでした")
    
    def _is_empty_or_comment_only(self, file_path: Path) -> bool:
        """ファイルが空またはコメントのみかチェック"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read().strip()
            
            # 空ファイル
            if not content:
                return True
            
            # ASTで解析してコメント・docstring以外があるかチェック
            try:
                tree = ast.parse(content)
                
                # モジュールレベルのdocstring以外に何かあるか
                for node in tree.body:
                    # docstringは最初のExpr(Str)ノード
                    if isinstance(node, ast.Expr) and isinstance(node.value, (ast.Str, ast.Constant)):
                        continue
                    # それ以外のノードがあれば空ではない
                    return False
                
                # docstringのみ、またはbodyが空
                return True
                
            except SyntaxError:
                # 構文エラーの場合は削除しない
                return False
                
        except Exception:
            # 読み取りエラーの場合は削除しない
            return False
    
    def _remove_empty_dirs(self):
        """空のディレクトリを深さ優先探索で削除"""
        print("\n📂 空のディレクトリを検索中...")
        
        # 深さ優先で処理するため、深いディレクトリから処理
        all_dirs = []
        for root, dirs, files in os.walk(self.target_dir, topdown=False):
            for d in dirs:
                all_dirs.append(Path(root) / d)
        
        # ディレクトリを深さ順（深い方から）にソート
        all_dirs.sort(key=lambda p: len(p.parts), reverse=True)
        
        for dir_path in all_dirs:
            if dir_path.exists() and self._is_empty_dir(dir_path):
                try:
                    dir_path.rmdir()
                    self.removed_dirs.append(dir_path)
                    print(f"  ✓ 削除: {dir_path.relative_to(self.target_dir.parent)}")
                except Exception as e:
                    print(f"  ✗ エラー: {dir_path} - {e}")
        
        if len([d for d in self.removed_dirs if d.name != '__pycache__']) == 0:
            print("  → 空のディレクトリは見つかりませんでした")
    
    def _is_empty_dir(self, dir_path: Path) -> bool:
        """ディレクトリが空かチェック"""
        try:
            # ディレクトリ内のアイテムをチェック
            items = list(dir_path.iterdir())
            return len(items) == 0
        except:
            return False
    
    def _print_summary(self):
        """削除結果のサマリーを表示"""
        print("\n" + "=" * 60)
        print("🎉 クリーンアップ完了！")
        print("=" * 60)
        
        total_removed = len(self.removed_files) + len(self.removed_dirs) + len(self.empty_init_files)
        
        if total_removed == 0:
            print("削除対象のファイル・ディレクトリはありませんでした。")
        else:
            print(f"削除されたアイテム数: {total_removed}")
            
            if self.removed_dirs:
                pycache_count = len([d for d in self.removed_dirs if d.name == '__pycache__'])
                empty_dir_count = len(self.removed_dirs) - pycache_count
                
                if pycache_count > 0:
                    print(f"  - __pycache__ディレクトリ: {pycache_count}個")
                if empty_dir_count > 0:
                    print(f"  - 空のディレクトリ: {empty_dir_count}個")
            
            if self.empty_init_files:
                print(f"  - 空の__init__.pyファイル: {len(self.empty_init_files)}個")


def main():
    """メイン関数"""
    # プロジェクトルートとsrcディレクトリを設定
    project_root = Path(__file__).parent.parent.parent
    src_dir = project_root / "src"
    
    if not src_dir.exists():
        print(f"❌ エラー: {src_dir} が見つかりません")
        return 1
    
    # 対象を表示
    print(f"🔍 対象ディレクトリ: {src_dir}")
    print("\n削除対象:")
    print("  1. すべての__pycache__ディレクトリ")
    print("  2. コメントのみの__init__.pyファイル")
    print("  3. 空のディレクトリ")
    
    # クリーナーを実行
    cleaner = UnnecessaryFileCleaner(src_dir)
    cleaner.clean()
    
    return 0


if __name__ == "__main__":
    exit(main())