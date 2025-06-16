"""状態管理システムのインターフェース

設定システムから分離された実行時状態管理
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class ExecutionHistory:
    """実行履歴データ"""
    contest_name: str
    problem_name: str
    language: str
    env_type: str
    timestamp: str
    success: bool


@dataclass
class SessionContext:
    """セッションコンテキスト"""
    current_contest: str
    current_problem: str
    current_language: str
    previous_contest: str
    previous_problem: str
    user_specified_fields: Dict[str, bool]  # どのフィールドがユーザー指定か


class IStateManager(ABC):
    """状態管理システムのインターフェース
    
    runtimeレイヤーから分離された純粋な状態管理
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
    def get_execution_history(self, limit: int = 10) -> list[ExecutionHistory]:
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