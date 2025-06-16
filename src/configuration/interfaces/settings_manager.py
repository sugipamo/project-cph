"""設定管理の統一インターフェース

runtimeレイヤー分離のための設定管理抽象化
"""
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

from .execution_settings import IExecutionSettings
from .runtime_settings import IRuntimeSettings


class ISettingsManager(ABC):
    """設定管理の統一インターフェース

    設定システム（3層: system/shared/language）からruntime状態管理を分離
    """

    @abstractmethod
    def get_execution_settings(self) -> IExecutionSettings:
        """実行設定の取得

        Returns:
            実行設定インターフェース
        """
        pass

    @abstractmethod
    def get_runtime_settings(self, language: str) -> IRuntimeSettings:
        """Runtime設定の取得

        Args:
            language: 言語名

        Returns:
            Runtime設定インターフェース
        """
        pass

    @abstractmethod
    def save_execution_context(self, context: Dict[str, Any]) -> None:
        """実行コンテキストの保存

        Args:
            context: 保存するコンテキスト情報
        """
        pass

    @abstractmethod
    def load_execution_context(self) -> Optional[Dict[str, Any]]:
        """実行コンテキストの読み込み

        Returns:
            保存されたコンテキスト情報
        """
        pass

    @abstractmethod
    def expand_template(self, template: str, context: Dict[str, str]) -> str:
        """テンプレート展開

        Args:
            template: 展開するテンプレート文字列
            context: 展開用の変数辞書

        Returns:
            展開された文字列
        """
        pass
