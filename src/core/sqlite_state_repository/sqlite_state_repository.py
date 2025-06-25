"""SQLiteベースの状態管理実装

Infrastructure層での状態永続化の具体実装
"""
from typing import Any, Dict, Optional
from sqlite.repositories.system_config_repository import SystemConfigRepository
from repositories.interfaces.state_repository import IStateRepository
from repositories.models.execution_history import ExecutionHistory
from repositories.models.session_context import SessionContext

class SqliteStateRepository(IStateRepository):
    """SQLiteベースの状態管理実装

    設定データではなく実行時状態を管理する専用システム
    SystemConfigRepositoryを利用するが、明確に分離されたカテゴリを使用
    """

    def __init__(self, config_repo: SystemConfigRepository, json_provider):
        self.config_repo = config_repo
        self._session_category = 'session_state'
        self._history_category = 'execution_history'
        self._user_values_category = 'user_specified'
        self._json_provider = json_provider

    def save_execution_history(self, history: ExecutionHistory) -> None:
        """実行履歴の保存"""
        history_data = {'contest_name': history.contest_name, 'problem_name': history.problem_name, 'language': history.language, 'env_type': history.env_type, 'timestamp': history.timestamp, 'success': history.success}
        key = f'history_{history.timestamp}'
        value = self._json_provider.dumps(history_data)
        self.config_repo.save_config(key=key, value=value, category=self._history_category, description=f'Execution history for {history.contest_name}_{history.problem_name}')

    def get_execution_history(self, limit: int=10) -> list[ExecutionHistory]:
        """実行履歴の取得"""
        histories = self.config_repo.get_configs_by_category(self._history_category)
        result = []
        for config in sorted(histories, key=lambda x: x.key, reverse=True)[:limit]:
            if config.value:
                try:
                    data = self._json_provider.loads(config.value)
                    history = ExecutionHistory(contest_name=data['contest_name'], problem_name=data['problem_name'], language=data['language'], env_type=data['env_type'], timestamp=data['timestamp'], success=data['success'])
                    result.append(history)
                except (ValueError, TypeError, KeyError):
                    continue
        return result

    def save_session_context(self, context: SessionContext) -> None:
        """セッションコンテキストの保存"""
        context_data = {'current_contest': context.current_contest, 'current_problem': context.current_problem, 'current_language': context.current_language, 'previous_contest': context.previous_contest, 'previous_problem': context.previous_problem, 'user_specified_fields': context.user_specified_fields}
        value = self._json_provider.dumps(context_data)
        self.config_repo.save_config(key='current_session', value=value, category=self._session_category, description='Current session context')

    def load_session_context(self) -> Optional[SessionContext]:
        """セッションコンテキストの読み込み"""
        config = self.config_repo.get_config('current_session')
        if config and config.value:
            try:
                data = self._json_provider.loads(config.value)
                return SessionContext(current_contest=data['current_contest'], current_problem=data['current_problem'], current_language=data['current_language'], previous_contest=data['previous_contest'], previous_problem=data['previous_problem'], user_specified_fields=data['user_specified_fields'])
            except (ValueError, TypeError, KeyError):
                pass
        return None

    def save_user_specified_values(self, values: Dict[str, Any]) -> None:
        """ユーザー指定値の保存"""
        value = self._json_provider.dumps(values)
        self.config_repo.save_config(key='user_values', value=value, category=self._user_values_category, description='User specified values')

    def get_user_specified_values(self) -> Dict[str, Any]:
        """ユーザー指定値の取得"""
        config = self.config_repo.get_config('user_values')
        if config and config.value:
            try:
                return self._json_provider.loads(config.value)
            except (ValueError, TypeError):
                pass
        return {}

    def clear_session(self) -> None:
        """セッション情報のクリア"""
        session_configs = self.config_repo.get_configs_by_category(self._session_category)
        for config in session_configs:
            self.config_repo.delete_config(config.key)