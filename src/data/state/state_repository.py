"""状態管理リポジトリのインターフェース

設定システムから分離された実行時状態管理
"""
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
from src.application.execution_history import ExecutionHistory
from src.infrastructure.persistence.state.models.session_context import SessionContext

class IStateRepository(ABC):
    """状態管理リポジトリのインターフェース

    Infrastructure層での状態永続化の抽象化
    設定データではなく実行時状態を管理
    """

    @abstractmethod
    def save_execution_history(self, history: ExecutionHistory) -> None:
        """実行履歴の保存

        Args:
            history: 保存する実行履歴
        """
        pass

    @abstractmethod
    def get_execution_history(self, limit: int=10) -> list[ExecutionHistory]:
        """実行履歴の取得

        Args:
            limit: 取得する履歴数

        Returns:
            実行履歴のリスト
        """
        pass

    @abstractmethod
    def save_session_context(self, context: SessionContext) -> None:
        """セッションコンテキストの保存

        Args:
            context: 保存するセッションコンテキスト
        """
        pass

    @abstractmethod
    def load_session_context(self) -> Optional[SessionContext]:
        """セッションコンテキストの読み込み

        Returns:
            保存されたセッションコンテキスト
        """
        pass

    @abstractmethod
    def save_user_specified_values(self, values: Dict[str, Any]) -> None:
        """ユーザー指定値の保存

        Args:
            values: 保存するユーザー指定値
        """
        pass

    @abstractmethod
    def get_user_specified_values(self) -> Dict[str, Any]:
        """ユーザー指定値の取得

        Returns:
            保存されたユーザー指定値
        """
        pass

    @abstractmethod
    def clear_session(self) -> None:
        """セッション情報のクリア"""
        pass