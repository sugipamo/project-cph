"""
パス操作に関するユーティリティ関数
"""
from pathlib import Path
import os


class PathUtil:
    """パス操作のユーティリティクラス"""
    
    @staticmethod
    def resolve_path(base_dir, path):
        """
        ベースディレクトリを基準にパスを解決する
        
        Args:
            base_dir: ベースディレクトリ
            path: 対象パス
            
        Returns:
            解決されたパス
        """
        base = Path(base_dir)
        target = Path(path)
        
        if target.is_absolute():
            return target
        return base / target
    
    @staticmethod
    def ensure_parent_dir(path):
        """
        指定されたパスの親ディレクトリを作成する
        
        Args:
            path: 対象パス
        """
        parent = Path(path).parent
        parent.mkdir(parents=True, exist_ok=True)
    
    @staticmethod
    def normalize_path(path):
        """
        パスを正規化する
        
        Args:
            path: 対象パス
            
        Returns:
            正規化されたパス
        """
        return Path(path).resolve()
    
    @staticmethod
    def get_relative_path(base_dir, target_path):
        """
        ベースディレクトリからの相対パスを取得する
        
        Args:
            base_dir: ベースディレクトリ
            target_path: 対象パス
            
        Returns:
            相対パス
        """
        base = Path(base_dir).resolve()
        target = Path(target_path).resolve()
        
        try:
            return target.relative_to(base)
        except ValueError:
            # relative_toで計算できない場合は絶対パスを返す
            return target
    
    @staticmethod
    def is_subdirectory(parent_dir, child_path):
        """
        指定されたパスが親ディレクトリのサブディレクトリかどうかを判定する
        
        Args:
            parent_dir: 親ディレクトリ
            child_path: 子パス
            
        Returns:
            サブディレクトリの場合True
        """
        try:
            parent = Path(parent_dir).resolve()
            child = Path(child_path).resolve()
            child.relative_to(parent)
            return True
        except ValueError:
            return False
    
    @staticmethod
    def safe_path_join(*paths):
        """
        安全にパスを結合する（パストラバーサル攻撃を防ぐ）
        
        Args:
            *paths: 結合するパス
            
        Returns:
            結合されたパス
            
        Raises:
            ValueError: 不正なパスが含まれている場合
        """
        result = Path(paths[0])
        
        for path in paths[1:]:
            path_part = Path(path)
            
            # 絶対パスや親ディレクトリへの参照をチェック
            if path_part.is_absolute() or '..' in path_part.parts:
                raise ValueError(f"Unsafe path component: {path}")
            
            result = result / path_part
        
        return result
    
    @staticmethod
    def get_file_extension(path):
        """
        ファイルの拡張子を取得する
        
        Args:
            path: ファイルパス
            
        Returns:
            拡張子（ドット付き）
        """
        return Path(path).suffix
    
    @staticmethod
    def change_extension(path, new_extension):
        """
        ファイルの拡張子を変更する
        
        Args:
            path: 元のファイルパス
            new_extension: 新しい拡張子（ドット付きまたはなし）
            
        Returns:
            拡張子を変更したパス
        """
        path_obj = Path(path)
        if not new_extension.startswith('.'):
            new_extension = '.' + new_extension
        return path_obj.with_suffix(new_extension)