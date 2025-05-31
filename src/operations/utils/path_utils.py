"""
パス操作に関するユーティリティ関数
"""
from pathlib import Path
import os
from typing import Any, Dict, List
from src.context.resolver.config_resolver import ConfigNode, resolve_best


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
            
        パフォーマンス最適化:
        - 例外ベースの制御フローからrelative_to()へ変更
        - より効率的なパス解決
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


# Configuration-based path resolution functions

def get_workspace_path(resolver: ConfigNode, language: str) -> Path:
    """Get workspace path from configuration."""
    node = resolve_best(resolver, [language, "workspace_path"])
    if node is None or node.value is None or node.key != "workspace_path":
        raise TypeError("workspace_pathが設定されていません")
    return Path(node.value)


def get_contest_current_path(resolver: ConfigNode, language: str) -> Path:
    """Get contest current path from configuration."""
    node = resolve_best(resolver, [language, "contest_current_path"])
    if node is None or node.value is None or node.key != "contest_current_path":
        raise TypeError("contest_current_pathが設定されていません")
    return Path(node.value)


def get_contest_env_path() -> Path:
    """Get contest_env path by searching up directory tree."""
    cur = os.path.abspath(os.getcwd())
    while True:
        candidate = os.path.join(cur, "contest_env")
        if os.path.isdir(candidate):
            return Path(candidate)
        parent = os.path.dirname(cur)
        if parent == cur:
            break
        cur = parent
    raise ValueError("contest_env_pathが自動検出できませんでした。contest_envディレクトリが見つかりません。")


def get_contest_template_path(resolver: ConfigNode, language: str) -> Path:
    """Get contest template path from configuration."""
    node = resolve_best(resolver, [language, "contest_template_path"])
    if node is None or node.key != "contest_template_path" or node.value is None:
        raise TypeError("contest_template_pathが設定されていません")
    return Path(node.value)


def get_contest_temp_path(resolver: ConfigNode, language: str) -> Path:
    """Get contest temp path from configuration."""
    node = resolve_best(resolver, [language, "contest_temp_path"])
    if node is None or node.key != "contest_temp_path" or node.value is None:
        raise TypeError("contest_temp_pathが設定されていません")
    return Path(node.value)


def get_test_case_path(contest_current_path: Path) -> Path:
    """Get test case directory path."""
    return contest_current_path / "test"


def get_test_case_in_path(contest_current_path: Path) -> Path:
    """Get test case input directory path."""
    return get_test_case_path(contest_current_path) / "in"


def get_test_case_out_path(contest_current_path: Path) -> Path:
    """Get test case output directory path."""
    return get_test_case_path(contest_current_path) / "out"


def get_source_file_name(resolver: ConfigNode, language: str) -> str:
    """Get source file name from configuration using resolve."""
    node = resolve_best(resolver, [language, "source_file_name"])
    if node is None or node.key != "source_file_name" or node.value is None:
        raise ValueError("source_file_nameが設定されていません")
    return str(node.value)