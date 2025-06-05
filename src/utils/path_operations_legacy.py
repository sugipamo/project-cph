"""
パス操作ライブラリの互換性レイヤー
既存コードとの後方互換性を維持するためのラッパー

このモジュールは段階的移行期間中に使用されます：
- 既存のPathUtilクラスAPIを維持
- 既存の純粋関数APIを維持  
- 新しい統合APIへの透明な移行を提供

注意: このモジュールは非推奨（deprecated）であり、将来的に削除される予定です。
新しいコードでは src.utils.path_operations.PathOperations を直接使用してください。
"""
import warnings
from typing import Any, Dict, List, Union, Optional, Tuple
from pathlib import Path

# 新しい統合ライブラリをインポート
from src.utils.path_operations import PathOperations, DockerPathOperations, PathOperationResult


def _deprecated_warning(old_function: str, new_function: str):
    """非推奨警告を表示"""
    warnings.warn(
        f"{old_function} is deprecated. Use {new_function} instead.",
        DeprecationWarning,
        stacklevel=3
    )


class PathUtil:
    """従来のPathUtilクラスとの互換性を保つラッパー
    
    注意: このクラスは非推奨です。新しいコードでは
    src.utils.path_operations.PathOperations を使用してください。
    """
    
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
        _deprecated_warning(
            "PathUtil.resolve_path()",
            "PathOperations.resolve_path()"
        )
        return PathOperations.resolve_path(base_dir, path, strict=False)
    
    @staticmethod
    def ensure_parent_dir(path):
        """
        指定されたパスの親ディレクトリを作成する
        
        Args:
            path: 対象パス
        """
        _deprecated_warning(
            "PathUtil.ensure_parent_dir()",
            "PathOperations.ensure_parent_dir()"
        )
        return PathOperations.ensure_parent_dir(path)
    
    @staticmethod
    def normalize_path(path):
        """
        パスを正規化する
        
        Args:
            path: 対象パス
            
        Returns:
            正規化されたパス
        """
        _deprecated_warning(
            "PathUtil.normalize_path()",
            "PathOperations.normalize_path()"
        )
        return PathOperations.normalize_path(path, strict=False)
    
    @staticmethod
    def get_relative_path(path, base):
        """
        ベースパスからの相対パスを取得する
        
        Args:
            path: 対象パス
            base: ベースパス
            
        Returns:
            相対パス
        """
        _deprecated_warning(
            "PathUtil.get_relative_path()",
            "PathOperations.get_relative_path()"
        )
        return PathOperations.get_relative_path(path, base, strict=False)
    
    @staticmethod
    def is_subdirectory(path, parent):
        """
        パスが指定された親ディレクトリのサブディレクトリかチェック
        
        Args:
            path: チェック対象パス
            parent: 親ディレクトリパス
            
        Returns:
            bool: サブディレクトリの場合True
        """
        _deprecated_warning(
            "PathUtil.is_subdirectory()",
            "PathOperations.is_subdirectory()"
        )
        return PathOperations.is_subdirectory(path, parent, strict=False)
    
    @staticmethod
    def safe_path_join(*paths):
        """
        安全にパスを結合する
        
        Args:
            *paths: 結合するパス要素
            
        Returns:
            結合されたパス
        """
        _deprecated_warning(
            "PathUtil.safe_path_join()",
            "PathOperations.safe_path_join()"
        )
        return PathOperations.safe_path_join(*paths, strict=False)
    
    @staticmethod
    def get_file_extension(path):
        """
        ファイルの拡張子を取得する
        
        Args:
            path: 対象パス
            
        Returns:
            拡張子（ドット付き）
        """
        _deprecated_warning(
            "PathUtil.get_file_extension()",
            "PathOperations.get_file_extension()"
        )
        return PathOperations.get_file_extension(path, strict=False)
    
    @staticmethod
    def change_extension(path, new_extension):
        """
        ファイルの拡張子を変更する
        
        Args:
            path: 対象パス
            new_extension: 新しい拡張子
            
        Returns:
            新しいパス
        """
        _deprecated_warning(
            "PathUtil.change_extension()",
            "PathOperations.change_extension()"
        )
        return PathOperations.change_extension(path, new_extension, strict=False)


# 純粋関数の互換性ラッパー
def resolve_path_pure(base_dir: str, path: str) -> PathOperationResult:
    """純粋関数版のパス解決（互換性ラッパー）
    
    注意: この関数は非推奨です。
    PathOperations.resolve_path(strict=True) を使用してください。
    """
    _deprecated_warning(
        "resolve_path_pure()",
        "PathOperations.resolve_path(strict=True)"
    )
    return PathOperations.resolve_path(base_dir, path, strict=True)


def normalize_path_pure(path: str) -> PathOperationResult:
    """純粋関数版のパス正規化（互換性ラッパー）
    
    注意: この関数は非推奨です。
    PathOperations.normalize_path(strict=True) を使用してください。
    """
    _deprecated_warning(
        "normalize_path_pure()",
        "PathOperations.normalize_path(strict=True)"
    )
    return PathOperations.normalize_path(path, strict=True)


def get_relative_path_pure(path: str, base: str) -> PathOperationResult:
    """純粋関数版の相対パス取得（互換性ラッパー）
    
    注意: この関数は非推奨です。
    PathOperations.get_relative_path(strict=True) を使用してください。
    """
    _deprecated_warning(
        "get_relative_path_pure()",
        "PathOperations.get_relative_path(strict=True)"
    )
    return PathOperations.get_relative_path(path, base, strict=True)


def is_subdirectory_pure(path: str, parent: str) -> Tuple[bool, PathOperationResult]:
    """純粋関数版のサブディレクトリ判定（互換性ラッパー）
    
    注意: この関数は非推奨です。
    PathOperations.is_subdirectory(strict=True) を使用してください。
    """
    _deprecated_warning(
        "is_subdirectory_pure()",
        "PathOperations.is_subdirectory(strict=True)"
    )
    return PathOperations.is_subdirectory(path, parent, strict=True)


def safe_path_join_pure(*paths: str) -> PathOperationResult:
    """純粋関数版の安全なパス結合（互換性ラッパー）
    
    注意: この関数は非推奨です。
    PathOperations.safe_path_join(strict=True) を使用してください。
    """
    _deprecated_warning(
        "safe_path_join_pure()",
        "PathOperations.safe_path_join(strict=True)"
    )
    return PathOperations.safe_path_join(*paths, strict=True)


# Docker関数の互換性ラッパー
def convert_path_to_docker_mount(path: str, workspace_path: str, mount_path: str) -> str:
    """Docker パス変換（互換性ラッパー）
    
    注意: この関数は非推奨です。
    DockerPathOperations.convert_path_to_docker_mount() を使用してください。
    """
    _deprecated_warning(
        "convert_path_to_docker_mount()",
        "DockerPathOperations.convert_path_to_docker_mount()"
    )
    return DockerPathOperations.convert_path_to_docker_mount(path, workspace_path, mount_path)


def get_docker_mount_path_from_config(env_json: Dict, language: str, default_mount_path: str = "/workspace") -> str:
    """Docker マウントパス取得（互換性ラッパー）
    
    注意: この関数は非推奨です。
    DockerPathOperations.get_docker_mount_path_from_config() を使用してください。
    """
    _deprecated_warning(
        "get_docker_mount_path_from_config()",
        "DockerPathOperations.get_docker_mount_path_from_config()"
    )
    return DockerPathOperations.get_docker_mount_path_from_config(env_json, language, default_mount_path)


# 設定ベース関数（従来のpath_utils.pyから移植）
# これらの関数は ConfigNode に依存するため、別途移行が必要
try:
    from src.context.resolver.config_resolver import ConfigNode, resolve_best
    
    def get_workspace_path() -> str:
        """ワークスペースパスを取得（設定依存）
        
        注意: この関数は ConfigNode に依存しており、
        将来的に設定管理の統合と共に見直される予定です。
        """
        _deprecated_warning(
            "get_workspace_path()",
            "適切な設定管理システムへの移行を検討してください"
        )
        # ConfigNodeのインスタンスがないため、フォールバック値を返す
        return "."
    
    def get_contest_current_path() -> str:
        """現在のコンテストパスを取得（設定依存）
        
        注意: この関数は ConfigNode に依存しており、
        将来的に設定管理の統合と共に見直される予定です。
        """
        _deprecated_warning(
            "get_contest_current_path()",
            "適切な設定管理システムへの移行を検討してください"
        )
        # ConfigNodeのインスタンスがないため、フォールバック値を返す
        return "./contest_current"
    
    def get_test_case_path() -> str:
        """テストケースパスを取得（設定依存）
        
        注意: この関数は ConfigNode に依存しており、
        将来的に設定管理の統合と共に見直される予定です。
        """
        _deprecated_warning(
            "get_test_case_path()",
            "適切な設定管理システムへの移行を検討してください"
        )
        # ConfigNodeのインスタンスがないため、フォールバック値を返す
        return "./test"

except ImportError:
    # ConfigNode が利用できない場合のフォールバック
    import os
    
    def get_workspace_path() -> str:
        return os.getcwd()
    
    def get_contest_current_path() -> str:
        return "./contest_current"
    
    def get_test_case_path() -> str:
        return "./test"