"""実行設定のインターフェース

設定システム（system/shared/language）の抽象化
"""
from abc import ABC, abstractmethod
from typing import Dict, List


class IExecutionSettings(ABC):
    """実行設定のインターフェース
    
    contest_name, problem_name, language等の基本実行設定
    """
    
    @abstractmethod
    def get_contest_name(self) -> str:
        """コンテスト名の取得"""
        pass
    
    @abstractmethod
    def get_problem_name(self) -> str:
        """問題名の取得"""
        pass
    
    @abstractmethod
    def get_language(self) -> str:
        """言語名の取得"""
        pass
    
    @abstractmethod
    def get_env_type(self) -> str:
        """環境タイプの取得"""
        pass
    
    @abstractmethod
    def get_command_type(self) -> str:
        """コマンドタイプの取得"""
        pass
    
    @abstractmethod
    def get_old_contest_name(self) -> str:
        """前回のコンテスト名の取得"""
        pass
    
    @abstractmethod
    def get_old_problem_name(self) -> str:
        """前回の問題名の取得"""
        pass
    
    @abstractmethod
    def get_paths(self) -> Dict[str, str]:
        """パス設定の取得
        
        Returns:
            パス名とパス値の辞書
        """
        pass
    
    @abstractmethod
    def get_file_patterns(self) -> Dict[str, List[str]]:
        """ファイルパターンの取得
        
        Returns:
            パターン名とパターンリストの辞書
        """
        pass
    
    @abstractmethod
    def to_template_dict(self) -> Dict[str, str]:
        """テンプレート展開用辞書の取得
        
        Returns:
            変数名と値の辞書
        """
        pass