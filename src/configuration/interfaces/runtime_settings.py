"""Runtime設定のインターフェース

Runtime状態管理とは分離された設定データ
"""
from abc import ABC, abstractmethod
from typing import Any, Dict


class IRuntimeSettings(ABC):
    """Runtime設定のインターフェース

    language_id, source_file_name, run_command等のRuntime特化設定
    設定データのみでstate管理は含まない
    """

    @abstractmethod
    def get_language_id(self) -> str:
        """言語IDの取得（online-judge用）"""
        pass

    @abstractmethod
    def get_source_file_name(self) -> str:
        """ソースファイル名の取得"""
        pass

    @abstractmethod
    def get_run_command(self) -> str:
        """実行コマンドの取得"""
        pass

    @abstractmethod
    def get_timeout_seconds(self) -> int:
        """タイムアウト秒数の取得"""
        pass

    @abstractmethod
    def get_retry_settings(self) -> Dict[str, Any]:
        """リトライ設定の取得"""
        pass

    @abstractmethod
    def to_runtime_dict(self) -> Dict[str, str]:
        """Runtime用辞書の取得

        Returns:
            Runtime変数名と値の辞書
        """
        pass
