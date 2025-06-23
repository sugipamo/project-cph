"""システム操作関連の副作用モジュールの抽象化

os, sys などのシステム操作関連モジュールを
依存性注入可能な形で抽象化
"""
from abc import ABC, abstractmethod
from pathlib import Path
from typing import List, Optional, Union


class SystemOperations(ABC):
    """システム操作関連の副作用をまとめたインターフェース"""

    @abstractmethod
    def get_cwd(self) -> str:
        """カレントディレクトリを取得

        Returns:
            str: カレントディレクトリのパス
        """
        pass

    @abstractmethod
    def chdir(self, path: Union[str, Path]) -> None:
        """カレントディレクトリを変更

        Args:
            path: 変更先のディレクトリ
        """
        pass

    @abstractmethod
    def path_exists(self, path: Union[str, Path]) -> bool:
        """パスの存在確認

        Args:
            path: 確認するパス

        Returns:
            bool: 存在するか
        """
        pass

    @abstractmethod
    def is_file(self, path: Union[str, Path]) -> bool:
        """ファイルかどうか確認

        Args:
            path: 確認するパス

        Returns:
            bool: ファイルか
        """
        pass

    @abstractmethod
    def is_dir(self, path: Union[str, Path]) -> bool:
        """ディレクトリかどうか確認

        Args:
            path: 確認するパス

        Returns:
            bool: ディレクトリか
        """
        pass

    @abstractmethod
    def makedirs(self, path: Union[str, Path], exist_ok: bool) -> None:
        """ディレクトリを作成（親ディレクトリも含む）

        Args:
            path: 作成するディレクトリ
            exist_ok: 既存でもエラーにしないか
        """
        pass

    @abstractmethod
    def remove(self, path: Union[str, Path]) -> None:
        """ファイルを削除

        Args:
            path: 削除するファイル
        """
        pass

    @abstractmethod
    def rmdir(self, path: Union[str, Path]) -> None:
        """空のディレクトリを削除

        Args:
            path: 削除するディレクトリ
        """
        pass

    @abstractmethod
    def listdir(self, path: Union[str, Path]) -> List[str]:
        """ディレクトリの内容をリスト

        Args:
            path: リストするディレクトリ

        Returns:
            List[str]: ファイル/ディレクトリ名のリスト
        """
        pass

    @abstractmethod
    def get_env(self, key: str) -> Optional[str]:
        """環境変数を取得

        Args:
            key: 環境変数名

        Returns:
            Optional[str]: 環境変数の値（存在しない場合はNone）
        """
        pass

    @abstractmethod
    def set_env(self, key: str, value: str) -> None:
        """環境変数を設定

        Args:
            key: 環境変数名
            value: 設定する値
        """
        pass

    @abstractmethod
    def exit(self, code: int) -> None:
        """プログラムを終了

        Args:
            code: 終了コード
        """
        pass

    @abstractmethod
    def get_argv(self) -> List[str]:
        """コマンドライン引数を取得

        Returns:
            List[str]: コマンドライン引数のリスト
        """
        pass

    @abstractmethod
    def print_stdout(self, message: str) -> None:
        """標準出力にメッセージを出力

        Args:
            message: 出力するメッセージ
        """
        pass
