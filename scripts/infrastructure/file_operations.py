"""ファイル操作関連の副作用モジュールの抽象化

shutil, json, yaml などのファイル操作関連モジュールを
依存性注入可能な形で抽象化
"""
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, Union


class FileOperations(ABC):
    """ファイル操作関連の副作用をまとめたインターフェース"""

    @abstractmethod
    def copy_file(self, src: Union[str, Path], dst: Union[str, Path]) -> None:
        """ファイルをコピー

        Args:
            src: コピー元
            dst: コピー先
        """
        pass

    @abstractmethod
    def copy_tree(self, src: Union[str, Path], dst: Union[str, Path], dirs_exist_ok: bool) -> None:
        """ディレクトリツリーをコピー

        Args:
            src: コピー元
            dst: コピー先
            dirs_exist_ok: 既存ディレクトリがあってもエラーにしないか
        """
        pass

    @abstractmethod
    def move(self, src: Union[str, Path], dst: Union[str, Path]) -> None:
        """ファイル/ディレクトリを移動

        Args:
            src: 移動元
            dst: 移動先
        """
        pass

    @abstractmethod
    def remove_tree(self, path: Union[str, Path]) -> None:
        """ディレクトリツリーを削除

        Args:
            path: 削除するディレクトリ
        """
        pass

    @abstractmethod
    def load_json(self, file_path: Union[str, Path]) -> Dict[str, Any]:
        """JSONファイルを読み込み

        Args:
            file_path: JSONファイルパス

        Returns:
            Dict[str, Any]: JSONデータ
        """
        pass

    @abstractmethod
    def dump_json(self, data: Dict[str, Any], file_path: Union[str, Path], indent: int) -> None:
        """JSONファイルに書き込み

        Args:
            data: 書き込むデータ
            file_path: JSONファイルパス
            indent: インデント幅
        """
        pass

    @abstractmethod
    def load_yaml(self, file_path: Union[str, Path]) -> Dict[str, Any]:
        """YAMLファイルを読み込み

        Args:
            file_path: YAMLファイルパス

        Returns:
            Dict[str, Any]: YAMLデータ
        """
        pass

    @abstractmethod
    def dump_yaml(self, data: Dict[str, Any], file_path: Union[str, Path]) -> None:
        """YAMLファイルに書き込み

        Args:
            data: 書き込むデータ
            file_path: YAMLファイルパス
        """
        pass
