"""分離システムの統合テスト

設定システムと状態管理システムの統合動作テスト
"""
import os
import tempfile
from datetime import datetime
from unittest.mock import Mock, patch

import pytest

from src.configuration.adapters.unified_execution_adapter import UnifiedExecutionAdapter
from src.configuration.services.pure_settings_manager import PureSettingsManager
from src.infrastructure.persistence.sqlite.repositories.system_config_repository import SystemConfigRepository
from src.state.services.sqlite_state_manager import SqliteStateManager


class TestSeparatedSystemIntegration:
    """分離システムの統合テスト"""

    @pytest.fixture
    def temp_database(self):
        """テスト用の一時データベース"""
        with tempfile.NamedTemporaryFile(delete=False, suffix='.db') as tmp_file:
            db_path = tmp_file.name

        yield db_path

        # クリーンアップ
        if os.path.exists(db_path):
            os.unlink(db_path)

    @pytest.fixture
    def mock_config_loader(self):
        """ConfigurationLoaderのモック"""
        mock_loader = Mock()
        mock_config_source = Mock()

        # パス設定のモック
        mock_config_source.get_paths.return_value = {
            "contest_current_path": "./contest_current",
            "contest_stock_path": "./contest_stock/{language}/{contest}/{problem}",
            "contest_template_path": "./contest_template",
            "workspace_path": "./workspace"
        }

        # ファイルパターンのモック
        mock_config_source.get_file_patterns.return_value = {
            "contest_files": ["*.py", "*.cpp"],
            "test_files": ["*.txt", "*.in", "*.out"],
            "source_files": ["main.py", "main.cpp"]
        }

        mock_loader.load_configuration.return_value = mock_config_source
        return mock_loader

    @pytest.fixture
    def mock_language_registry(self):
        """LanguageRegistryのモック"""
        mock_registry = Mock()

        language_configs = {
            "python": {
                "language_id": "4006",
                "source_file_name": "main.py",
                "run_command": "python3",
                "timeout_seconds": 300,
                "retry_settings": {"max_attempts": 3, "delay": 1.0}
            },
            "cpp": {
                "language_id": "4003",
                "source_file_name": "main.cpp",
                "run_command": "g++ -o main main.cpp && ./main",
                "timeout_seconds": 600,
                "retry_settings": {"max_attempts": 3, "delay": 2.0}
            }
        }

        mock_registry.get_language_config.side_effect = lambda lang: language_configs.get(lang, language_configs["python"])
        return mock_registry

    @pytest.fixture
    def integrated_system(self, temp_database, mock_config_loader, mock_language_registry):
        """統合されたシステムのセットアップ"""
        # SystemConfigRepositoryのモック（簡略化）
        mock_config_repo = Mock()
        mock_config_repo.save_config = Mock()
        mock_config_repo.get_config = Mock(return_value=None)
        mock_config_repo.get_configs_by_category = Mock(return_value=[])
        mock_config_repo.delete_config = Mock()

        # 各コンポーネントの作成
        settings_manager = PureSettingsManager(mock_config_loader, mock_language_registry)
        state_manager = SqliteStateManager(mock_config_repo)
        unified_adapter = UnifiedExecutionAdapter(settings_manager, state_manager)

        return {
            "settings_manager": settings_manager,
            "state_manager": state_manager,
            "unified_adapter": unified_adapter,
            "config_repo": mock_config_repo
        }

    def test_complete_workflow_python(self, integrated_system):
        """Python言語での完全ワークフローテスト"""
        components = integrated_system
        adapter = components["unified_adapter"]

        # 1. システム初期化
        adapter.initialize(
            contest_name="abc300",
            problem_name="a",
            language="python",
            env_type="local",
            command_type="open"
        )

        # 2. 設定値の確認
        assert adapter.contest_name == "abc300"
        assert adapter.problem_name == "a"
        assert adapter.language == "python"
        assert adapter.env_type == "local"

        # 3. テンプレート展開のテスト
        template = "Contest: {contest_name}, Problem: {problem_name}, Language: {language}"
        result = adapter.format_string(template)
        expected = "Contest: abc300, Problem: a, Language: python"
        assert result == expected

        # 4. 設定辞書の取得
        config_dict = adapter.to_dict()
        assert config_dict["contest_name"] == "abc300"
        assert config_dict["language_id"] == "4006"
        assert config_dict["source_file_name"] == "main.py"
        assert config_dict["run_command"] == "python3"

        # 5. 実行結果の保存
        adapter.save_execution_result(success=True)

        # 6. StateManagerの状態確認
        components["config_repo"].save_config.assert_called()

    def test_complete_workflow_cpp(self, integrated_system):
        """C++言語での完全ワークフローテスト"""
        components = integrated_system
        adapter = components["unified_adapter"]

        # 1. システム初期化
        adapter.initialize(
            contest_name="abc301",
            problem_name="b",
            language="cpp",
            env_type="local",
            command_type="test"
        )

        # 2. 設定値の確認
        assert adapter.contest_name == "abc301"
        assert adapter.problem_name == "b"
        assert adapter.language == "cpp"
        assert adapter.command_type == "test"

        # 3. Runtime設定の確認
        config_dict = adapter.to_dict()
        assert config_dict["language_id"] == "4003"
        assert config_dict["source_file_name"] == "main.cpp"
        assert "g++" in config_dict["run_command"]

        # 4. パス展開のテスト
        paths_template = "{contest_stock_path}/{language}/{contest_name}/{problem_name}"
        result = adapter.format_string(paths_template)
        expected = "./contest_stock/{language}/{contest}/{problem}/cpp/abc301/b"
        assert result == expected

    def test_session_state_persistence(self, integrated_system):
        """セッション状態の永続化テスト"""
        components = integrated_system
        adapter = components["unified_adapter"]

        # 1. 最初のセッション
        adapter.initialize("abc300", "a", "python")

        # 2. StateManagerでセッション保存が呼ばれたことを確認
        components["state_manager"]
        # save_session_contextが内部で呼ばれることを間接的に確認
        components["config_repo"].save_config.assert_called()

    def test_multiple_language_switching(self, integrated_system):
        """複数言語間の切り替えテスト"""
        components = integrated_system
        settings_manager = components["settings_manager"]

        # 1. Python設定の取得
        python_runtime = settings_manager.get_runtime_settings("python")
        assert python_runtime.get_language_id() == "4006"
        assert python_runtime.get_source_file_name() == "main.py"

        # 2. C++設定の取得
        cpp_runtime = settings_manager.get_runtime_settings("cpp")
        assert cpp_runtime.get_language_id() == "4003"
        assert cpp_runtime.get_source_file_name() == "main.cpp"

        # 3. 設定の独立性確認（キャッシュテスト）
        python_runtime2 = settings_manager.get_runtime_settings("python")
        assert python_runtime2.get_language_id() == "4006"

    def test_template_expansion_with_file_patterns(self, integrated_system):
        """ファイルパターンを含むテンプレート展開テスト"""
        components = integrated_system
        adapter = components["unified_adapter"]
        settings_manager = components["settings_manager"]

        # 初期化
        adapter.initialize("abc300", "a", "python")

        # ファイルパターンのテンプレート展開
        # Note: 実際のファイルパターン展開は複雑なので、基本的な変数展開をテスト
        template = "{contest_current_path}/{source_file_name}"
        context = adapter.to_dict()
        result = settings_manager.expand_template(template, context)

        assert result == "./contest_current/main.py"

    def test_error_handling_missing_language(self, integrated_system):
        """存在しない言語に対するエラーハンドリングテスト"""
        components = integrated_system
        settings_manager = components["settings_manager"]

        # 存在しない言語でもデフォルト設定が返されることを確認
        unknown_runtime = settings_manager.get_runtime_settings("unknown_language")
        assert unknown_runtime.get_language_id() == "4006"  # デフォルトのpython設定
        assert unknown_runtime.get_source_file_name() == "main.py"


class TestSeparatedSystemVsLegacyComparison:
    """分離システムと既存システムの比較テスト"""

    def test_template_expansion_compatibility(self):
        """テンプレート展開の既存システムとの互換性テスト"""
        # 既存システムのシミュレーション
        legacy_context = {
            "contest_name": "abc300",
            "problem_name": "a",
            "language": "python",
            "language_id": "4006",
            "source_file_name": "main.py"
        }

        legacy_template = "Contest: {contest_name}, Problem: {problem_name}, File: {source_file_name}"
        legacy_result = legacy_template.format(**legacy_context)

        # 新システムでの同様の処理
        from tests.configuration.test_fixtures_separated_system import MockSettingsManager
        settings_manager = MockSettingsManager()

        new_result = settings_manager.expand_template(legacy_template, legacy_context)

        # 結果の一致確認
        assert new_result == legacy_result
        assert new_result == "Contest: abc300, Problem: a, File: main.py"

    def test_configuration_structure_compatibility(self):
        """設定構造の既存システムとの互換性テスト"""
        from tests.configuration.test_fixtures_separated_system import MockExecutionSettings, MockRuntimeSettings

        # 新システムの設定
        execution_settings = MockExecutionSettings("abc300", "a", "python")
        runtime_settings = MockRuntimeSettings("python")

        # 既存システムと同等の情報が取得できることを確認
        assert execution_settings.get_contest_name() == "abc300"
        assert execution_settings.get_problem_name() == "a"
        assert execution_settings.get_language() == "python"

        assert runtime_settings.get_language_id() == "4006"
        assert runtime_settings.get_source_file_name() == "main.py"
        assert runtime_settings.get_run_command() == "python3"

        # テンプレート辞書の互換性
        template_dict = execution_settings.to_template_dict()
        runtime_dict = runtime_settings.to_runtime_dict()

        # 既存システムで使用される重要なキーが存在することを確認
        expected_keys = {
            "contest_name", "problem_name", "language", "language_name",
            "env_type", "command_type"
        }
        assert expected_keys.issubset(set(template_dict.keys()))

        expected_runtime_keys = {
            "language_id", "source_file_name", "run_command", "timeout_seconds"
        }
        assert expected_runtime_keys.issubset(set(runtime_dict.keys()))

    def test_api_compatibility(self):
        """APIの既存システムとの互換性テスト"""
        from src.configuration.adapters.unified_execution_adapter import UnifiedExecutionAdapter
        from tests.configuration.test_fixtures_separated_system import MockSettingsManager, MockStateManager

        # 新システムのアダプター
        settings_manager = MockSettingsManager()
        state_manager = MockStateManager()
        adapter = UnifiedExecutionAdapter(settings_manager, state_manager)

        # 既存ExecutionContextAdapterと同様のAPIが利用可能であることを確認
        # Note: 実際の既存システムと完全に比較するには、既存システムのインスタンス化が必要

        # 基本的なAPIの存在確認
        assert hasattr(adapter, 'format_string')
        assert hasattr(adapter, 'to_dict')
        assert hasattr(adapter, 'to_format_dict')
        assert hasattr(adapter, 'initialize')

        # 初期化後のAPI動作確認
        adapter.initialize("abc300", "a", "python")

        # プロパティのアクセス確認（初期化後）
        assert hasattr(adapter, 'contest_name')
        assert hasattr(adapter, 'problem_name')
        assert hasattr(adapter, 'language')

        # 既存システムと同様の形式でデータが取得できることを確認
        config_dict = adapter.to_dict()
        assert isinstance(config_dict, dict)
        assert "contest_name" in config_dict
        assert "language_id" in config_dict

        # 文字列フォーマットが機能することを確認
        formatted = adapter.format_string("Test: {contest_name}")
        assert "abc300" in formatted
