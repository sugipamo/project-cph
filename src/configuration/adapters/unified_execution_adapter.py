"""統一実行アダプター

設定システムと状態管理システムを統合して既存インターフェースを提供
段階的移行のための互換性アダプター
"""
from typing import Dict, Any, Optional

from ..interfaces.settings_manager import ISettingsManager
from ..interfaces.execution_settings import IExecutionSettings
from ..interfaces.runtime_settings import IRuntimeSettings
from ...state.interfaces.state_manager import IStateManager, SessionContext, ExecutionHistory
from ..core.execution_configuration import ExecutionConfiguration
from ..expansion.template_expander import TemplateExpander


class UnifiedExecutionAdapter:
    """統一実行アダプター
    
    設定システム（PureSettingsManager）と状態管理システム（StateManager）を
    統合して、既存のExecutionContextAdapterと互換性を保つ
    """
    
    def __init__(self, settings_manager: ISettingsManager, state_manager: IStateManager):
        self.settings_manager = settings_manager
        self.state_manager = state_manager
        self._execution_settings: Optional[IExecutionSettings] = None
        self._runtime_settings: Optional[IRuntimeSettings] = None
    
    def initialize(self, contest_name: str, problem_name: str, language: str,
                   env_type: str = "local", command_type: str = "open") -> None:
        """アダプターの初期化
        
        Args:
            contest_name: コンテスト名
            problem_name: 問題名
            language: 言語名
            env_type: 環境タイプ
            command_type: コマンドタイプ
        """
        # 前回のセッションコンテキストを読み込み
        previous_context = self.state_manager.load_session_context()
        old_contest_name = previous_context.previous_contest if previous_context else ""
        old_problem_name = previous_context.previous_problem if previous_context else ""
        
        # 設定システムを初期化
        if hasattr(self.settings_manager, 'initialize'):
            self.settings_manager.initialize(
                contest_name=contest_name,
                problem_name=problem_name,
                language=language,
                env_type=env_type,
                command_type=command_type,
                old_contest_name=old_contest_name,
                old_problem_name=old_problem_name
            )
        
        # 実行設定とRuntime設定を取得
        self._execution_settings = self.settings_manager.get_execution_settings()
        self._runtime_settings = self.settings_manager.get_runtime_settings(language)
        
        # 新しいセッションコンテキストを保存
        new_context = SessionContext(
            current_contest=contest_name,
            current_problem=problem_name,
            current_language=language,
            previous_contest=old_contest_name,
            previous_problem=old_problem_name,
            user_specified_fields={}  # 実装時に指定フィールドを追跡
        )
        self.state_manager.save_session_context(new_context)
    
    # 既存ExecutionContextAdapterとの互換性メソッド
    
    def format_string(self, template: str) -> str:
        """既存のformat_stringメソッドの互換実装"""
        if not self._execution_settings:
            raise RuntimeError("Adapter not initialized")
        
        context = self.to_dict()
        return self.settings_manager.expand_template(template, context)
    
    def to_dict(self) -> Dict[str, str]:
        """既存のto_dictメソッドの互換実装"""
        if not self._execution_settings or not self._runtime_settings:
            raise RuntimeError("Adapter not initialized")
        
        # 実行設定から基本変数を取得
        template_dict = self._execution_settings.to_template_dict()
        
        # Runtime設定を追加
        runtime_dict = self._runtime_settings.to_runtime_dict()
        template_dict.update(runtime_dict)
        
        return template_dict
    
    def to_format_dict(self) -> Dict[str, str]:
        """既存のto_format_dictメソッドの互換実装"""
        return self.to_dict()
    
    # ExecutionConfigurationとの互換性プロパティ
    
    @property
    def contest_name(self) -> str:
        if not self._execution_settings:
            raise RuntimeError("Adapter not initialized")
        return self._execution_settings.get_contest_name()
    
    @property
    def problem_name(self) -> str:
        if not self._execution_settings:
            raise RuntimeError("Adapter not initialized")
        return self._execution_settings.get_problem_name()
    
    @property
    def language(self) -> str:
        if not self._execution_settings:
            raise RuntimeError("Adapter not initialized")
        return self._execution_settings.get_language()
    
    @property
    def env_type(self) -> str:
        if not self._execution_settings:
            raise RuntimeError("Adapter not initialized")
        return self._execution_settings.get_env_type()
    
    @property
    def command_type(self) -> str:
        if not self._execution_settings:
            raise RuntimeError("Adapter not initialized")
        return self._execution_settings.get_command_type()
    
    @property
    def old_contest_name(self) -> str:
        if not self._execution_settings:
            raise RuntimeError("Adapter not initialized")
        return self._execution_settings.get_old_contest_name()
    
    @property
    def old_problem_name(self) -> str:
        if not self._execution_settings:
            raise RuntimeError("Adapter not initialized")
        return self._execution_settings.get_old_problem_name()
    
    # 状態管理機能
    
    def save_execution_result(self, success: bool) -> None:
        """実行結果の保存"""
        if not self._execution_settings:
            return
        
        from datetime import datetime
        history = ExecutionHistory(
            contest_name=self._execution_settings.get_contest_name(),
            problem_name=self._execution_settings.get_problem_name(),
            language=self._execution_settings.get_language(),
            env_type=self._execution_settings.get_env_type(),
            timestamp=datetime.now().isoformat(),
            success=success
        )
        self.state_manager.save_execution_history(history)
    
    def get_execution_history(self, limit: int = 10):
        """実行履歴の取得"""
        return self.state_manager.get_execution_history(limit)
    
    # ExecutionConfigurationオブジェクトとの互換性のための変換
    
    def to_execution_configuration(self) -> ExecutionConfiguration:
        """既存のExecutionConfigurationオブジェクトへの変換
        
        Note: 既存システムとの互換性のために一時的に提供
        将来的には削除予定
        """
        if not self._execution_settings or not self._runtime_settings:
            raise RuntimeError("Adapter not initialized")
        
        # 必要な場合は既存のExecutionConfigurationを構築
        # ここでは簡略化のため例外を発生
        raise NotImplementedError(
            "to_execution_configuration() is deprecated. "
            "Use the adapter methods directly instead."
        )