"""
DFS探索によるmain.pyファイル発見モジュール
ファイル名降順でsrc_check全域を再帰的に探索
"""

import os
from pathlib import Path
from typing import List, NamedTuple


class ModuleInfo(NamedTuple):
    """発見されたmain.pyの情報"""
    path: Path
    module_name: str


class ModuleExplorer:
    """DFS探索でmain.pyを発見するクラス"""
    
    def __init__(self, base_path: Path):
        self.base_path = base_path
    
    def discover_main_modules(self) -> List[ModuleInfo]:
        """
        DFS探索でmain.pyを発見
        ファイル名降順で探索し、発見順でstackに保存
        """
        discovered_modules = []
        
        def dfs_search(current_path: Path):
            """深度優先探索でmain.pyを発見"""
            if not current_path.is_dir():
                return
            
            try:
                # ディレクトリ内のアイテムを取得し、ファイル名で降順ソート
                items = sorted(current_path.iterdir(), 
                             key=lambda x: x.name, 
                             reverse=True)
                
                # main.pyを先にチェック
                for item in items:
                    if item.is_file() and item.name == 'main.py':
                        # __pycache__やその他の無視すべきディレクトリをスキップ
                        # 自分自身（src_check直下のmain.py）は除外
                        if '__pycache__' not in str(item.parent) and item != self.base_path / 'main.py':
                            module_name = self._generate_module_name(item)
                            discovered_modules.append(ModuleInfo(item, module_name))
                
                # 次にディレクトリを再帰探索
                for item in items:
                    if item.is_dir() and not item.name.startswith('.') and item.name != '__pycache__':
                        dfs_search(item)
                        
            except PermissionError:
                # アクセス権限がない場合はスキップ
                pass
        
        dfs_search(self.base_path)
        return discovered_modules
    
    def _generate_module_name(self, main_py_path: Path) -> str:
        """
        main.pyファイルパスからモジュール名を生成
        例: src_check/processors/auto_correct/main.py -> auto_correct
        """
        parent_dir = main_py_path.parent
        relative_path = parent_dir.relative_to(self.base_path)
        
        # パス要素を取得
        parts = relative_path.parts
        
        if not parts:
            # src_check直下のmain.py
            return "root_main"
        
        # 最後のディレクトリ名をモジュール名として使用
        return parts[-1]
    
    def validate_module(self, module_path: Path) -> bool:
        """
        モジュールの有効性をチェック
        """
        if not module_path.exists():
            return False
        
        if not module_path.is_file():
            return False
        
        if module_path.name != 'main.py':
            return False
        
        # 基本的な構文チェック（簡易版）
        try:
            with open(module_path, 'r', encoding='utf-8') as f:
                content = f.read()
                # 空ファイルや極端に短いファイルは無効
                if len(content.strip()) < 10:
                    return False
                return True
        except (UnicodeDecodeError, IOError):
            return False