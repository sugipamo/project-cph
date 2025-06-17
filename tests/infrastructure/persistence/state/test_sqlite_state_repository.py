"""SqliteStateRepository の単体テスト

Infrastructure層での状態管理の分離後のテスト
"""
import json
from datetime import datetime
from unittest.mock import MagicMock, Mock

import pytest

from src.infrastructure.persistence.state import ExecutionHistory, SessionContext, SqliteStateRepository
from tests.configuration.test_fixtures_separated_system import sample_execution_history, sample_session_context


class TestSqliteStateRepository:
    """SqliteStateRepositoryの単体テスト"""

    @pytest.fixture
    def mock_config_repo(self):
        """MockのSystemConfigRepositoryを作成"""
        mock_repo = Mock()
        mock_repo.save_config = Mock()
        mock_repo.get_config = Mock()
        mock_repo.get_configs_by_category = Mock()
        mock_repo.delete_config = Mock()
        return mock_repo

    @pytest.fixture
    def state_repository(self, mock_config_repo):
        """SqliteStateRepositoryのインスタンスを作成"""
        return SqliteStateRepository(mock_config_repo)

    def test_save_execution_history(self, state_repository, mock_config_repo, sample_execution_history):
        """実行履歴の保存をテスト"""
        state_repository.save_execution_history(sample_execution_history)

        # save_configが正しい引数で呼ばれたかチェック
        mock_config_repo.save_config.assert_called_once()
        args = mock_config_repo.save_config.call_args

        # キーの形式チェック
        assert args[1]['key'].startswith('history_')
        assert args[1]['category'] == 'execution_history'

        # 保存されたデータの内容チェック
        saved_data = json.loads(args[1]['value'])
        assert saved_data['contest_name'] == sample_execution_history.contest_name
        assert saved_data['problem_name'] == sample_execution_history.problem_name
        assert saved_data['language'] == sample_execution_history.language

    def test_get_execution_history_empty(self, state_repository, mock_config_repo):
        """空の実行履歴の取得をテスト"""
        mock_config_repo.get_configs_by_category.return_value = []

        histories = state_repository.get_execution_history()

        assert histories == []
        mock_config_repo.get_configs_by_category.assert_called_once_with('execution_history')

    def test_get_execution_history_with_data(self, state_repository, mock_config_repo, sample_execution_history):
        """データありの実行履歴の取得をテスト"""
        # MockのConfigオブジェクトを作成
        mock_config = Mock()
        mock_config.key = 'history_2023-01-01T10:00:00'
        mock_config.value = json.dumps({
            'contest_name': sample_execution_history.contest_name,
            'problem_name': sample_execution_history.problem_name,
            'language': sample_execution_history.language,
            'env_type': sample_execution_history.env_type,
            'timestamp': sample_execution_history.timestamp,
            'success': sample_execution_history.success
        })

        mock_config_repo.get_configs_by_category.return_value = [mock_config]

        histories = state_repository.get_execution_history()

        assert len(histories) == 1
        history = histories[0]
        assert history.contest_name == sample_execution_history.contest_name
        assert history.problem_name == sample_execution_history.problem_name
        assert history.language == sample_execution_history.language

    def test_get_execution_history_with_invalid_data(self, state_repository, mock_config_repo):
        """無効なデータを含む実行履歴の取得をテスト"""
        # 無効なJSONを持つMockオブジェクト
        mock_config = Mock()
        mock_config.key = 'history_invalid'
        mock_config.value = 'invalid json'

        mock_config_repo.get_configs_by_category.return_value = [mock_config]

        histories = state_repository.get_execution_history()

        # 無効なデータはスキップされる
        assert histories == []

    def test_save_session_context(self, state_repository, mock_config_repo, sample_session_context):
        """セッションコンテキストの保存をテスト"""
        state_repository.save_session_context(sample_session_context)

        mock_config_repo.save_config.assert_called_once()
        args = mock_config_repo.save_config.call_args

        assert args[1]['key'] == 'current_session'
        assert args[1]['category'] == 'session_state'

        # 保存されたデータの内容チェック
        saved_data = json.loads(args[1]['value'])
        assert saved_data['current_contest'] == sample_session_context.current_contest
        assert saved_data['current_problem'] == sample_session_context.current_problem

    def test_load_session_context_none(self, state_repository, mock_config_repo):
        """セッションコンテキストが存在しない場合のテスト"""
        mock_config_repo.get_config.return_value = None

        context = state_repository.load_session_context()

        assert context is None
        mock_config_repo.get_config.assert_called_once_with('current_session')

    def test_load_session_context_with_data(self, state_repository, mock_config_repo, sample_session_context):
        """セッションコンテキストが存在する場合のテスト"""
        mock_config = Mock()
        mock_config.value = json.dumps({
            'current_contest': sample_session_context.current_contest,
            'current_problem': sample_session_context.current_problem,
            'current_language': sample_session_context.current_language,
            'previous_contest': sample_session_context.previous_contest,
            'previous_problem': sample_session_context.previous_problem,
            'user_specified_fields': sample_session_context.user_specified_fields
        })

        mock_config_repo.get_config.return_value = mock_config

        context = state_repository.load_session_context()

        assert context is not None
        assert context.current_contest == sample_session_context.current_contest
        assert context.current_problem == sample_session_context.current_problem

    def test_save_user_specified_values(self, state_repository, mock_config_repo):
        """ユーザー指定値の保存をテスト"""
        values = {'language': 'python', 'contest': 'abc123'}

        state_repository.save_user_specified_values(values)

        mock_config_repo.save_config.assert_called_once()
        args = mock_config_repo.save_config.call_args

        assert args[1]['key'] == 'user_values'
        assert args[1]['category'] == 'user_specified'

        saved_data = json.loads(args[1]['value'])
        assert saved_data == values

    def test_get_user_specified_values_empty(self, state_repository, mock_config_repo):
        """ユーザー指定値が空の場合のテスト"""
        mock_config_repo.get_config.return_value = None

        values = state_repository.get_user_specified_values()

        assert values == {}

    def test_get_user_specified_values_with_data(self, state_repository, mock_config_repo):
        """ユーザー指定値がある場合のテスト"""
        expected_values = {'language': 'python', 'contest': 'abc123'}

        mock_config = Mock()
        mock_config.value = json.dumps(expected_values)
        mock_config_repo.get_config.return_value = mock_config

        values = state_repository.get_user_specified_values()

        assert values == expected_values

    def test_clear_session(self, state_repository, mock_config_repo):
        """セッション情報のクリアをテスト"""
        # セッション関連の設定をMock
        mock_configs = [Mock(), Mock()]
        mock_configs[0].key = 'session_key1'
        mock_configs[1].key = 'session_key2'

        mock_config_repo.get_configs_by_category.return_value = mock_configs

        state_repository.clear_session()

        mock_config_repo.get_configs_by_category.assert_called_once_with('session_state')

        # 各設定が削除されたかチェック
        assert mock_config_repo.delete_config.call_count == 2
        mock_config_repo.delete_config.assert_any_call('session_key1')
        mock_config_repo.delete_config.assert_any_call('session_key2')


class TestStateModels:
    """状態管理のデータモデルテスト"""

    def test_execution_history_creation(self, sample_execution_history):
        """ExecutionHistoryの作成をテスト"""
        history = sample_execution_history

        assert history.contest_name == 'abc300'
        assert history.problem_name == 'a'
        assert history.language == 'python'
        assert history.env_type == 'local'
        assert isinstance(history.success, bool)

    def test_session_context_creation(self, sample_session_context):
        """SessionContextの作成をテスト"""
        context = sample_session_context

        assert context.current_contest == 'abc300'
        assert context.current_problem == 'a'
        assert context.current_language == 'python'
        assert isinstance(context.user_specified_fields, dict)
