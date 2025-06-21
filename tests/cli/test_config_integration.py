"""設定ファイル読み込みの動作確認テスト"""
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src.cli.cli_app import MinimalCLIApp
from src.configuration.config_manager import TypeSafeConfigNodeManager
from src.workflow.workflow_result import WorkflowExecutionResult


class TestConfigFileLoading:
    """設定ファイル読み込みの動作確認テスト"""

    @patch('src.cli.cli_app.parse_user_input')
    @patch('src.cli.cli_app.WorkflowExecutionService')
    def test_config_system_integration(self, mock_service_class, mock_parse):
        """設定システム統合の基本テスト"""
        # モックのセットアップ
        mock_logger = MagicMock()
        mock_infrastructure = MagicMock()
        mock_context = MagicMock()
        mock_service = MagicMock()
        mock_result = WorkflowExecutionResult(
            success=True, results=[], preparation_results=[], errors=[], warnings=[]
        )

        # 設定システムが正常動作することをシミュレート
        mock_parse.return_value = mock_context
        mock_service_class.return_value = mock_service
        mock_service.execute_workflow.return_value = mock_result

        # テスト実行
        app = MinimalCLIApp(infrastructure=mock_infrastructure, logger=mock_logger)
        result = app.run_cli_application(["python", "test", "abc301", "a"])

        # 設定システムを経由してparse_user_inputが呼ばれることを確認
        mock_parse.assert_called_once_with(["python", "test", "abc301", "a"], mock_infrastructure)
        assert result == 0

    def test_config_manager_initialization(self):
        """TypeSafeConfigNodeManagerの初期化テスト"""
        # モックのインフラストラクチャを作成
        mock_infrastructure = MagicMock()

        # 実際の設定マネージャーを作成
        config_manager = TypeSafeConfigNodeManager(mock_infrastructure)

        # 初期化が成功することを確認
        assert config_manager is not None
        assert hasattr(config_manager, 'load_from_files')
        assert hasattr(config_manager, 'resolve_config')

    def test_system_config_files_exist(self):
        """システム設定ファイルの存在確認"""
        config_dir = Path("config/system")

        # 必要な設定ファイルの存在確認
        required_files = [
            "dev_config.json",
            "docker_defaults.json",
            "docker_security.json",
            "system_constants.json"
        ]

        for filename in required_files:
            config_file = config_dir / filename
            assert config_file.exists(), f"設定ファイル {filename} が見つかりません"

    def test_config_file_json_validity(self):
        """設定ファイルのJSON形式確認"""
        import json

        config_dir = Path("config/system")
        config_files = list(config_dir.glob("*.json"))

        assert len(config_files) > 0, "設定ファイルが見つかりません"

        for config_file in config_files:
            with open(config_file, encoding='utf-8') as f:
                try:
                    data = json.load(f)
                    assert isinstance(data, dict), f"{config_file} は辞書形式ではありません"
                except json.JSONDecodeError as e:
                    pytest.fail(f"設定ファイル {config_file} のJSON形式が不正です: {e}")

    @patch('src.context.user_input_parser.user_input_parser.TypeSafeConfigNodeManager')
    def test_config_manager_loading_in_parser(self, mock_config_manager_class):
        """user_input_parser内での設定マネージャー使用テスト"""
        from src.context.user_input_parser.user_input_parser import _create_execution_config

        mock_config_manager = MagicMock()
        mock_config_manager_class.return_value = mock_config_manager

        # モック実行設定を作成
        mock_execution_config = MagicMock()
        mock_config_manager.create_execution_config.return_value = mock_execution_config

        # テスト実行
        result = _create_execution_config(
            command_type="test",
            language="python",
            contest_name="abc301",
            problem_name="a",
            env_type="local"
        )

        # 設定マネージャーが正しく使用されることを確認
        mock_config_manager.load_from_files.assert_called_once_with(
            system_dir="./config/system",
            env_dir="contest_env",
            language="python"
        )

        mock_config_manager.create_execution_config.assert_called_once_with(
            contest_name="abc301",
            problem_name="a",
            language="python",
            env_type="local",
            command_type="test"
        )

        assert result is mock_execution_config


class TestConfigLoadingPaths:
    """設定ファイルパスのテスト"""

    def test_system_config_path_resolution(self):
        """システム設定パスの解決テスト"""
        from src.infrastructure.di_container import DIContainer
        infrastructure = DIContainer()
        TypeSafeConfigNodeManager(infrastructure)

        # システム設定ディレクトリの確認
        system_dir = Path("config/system")
        assert system_dir.exists(), "システム設定ディレクトリが存在しません"
        assert system_dir.is_dir(), "システム設定パスがディレクトリではありません"

    def test_contest_env_structure(self):
        """contest_env構造の確認"""
        contest_env_dir = Path("contest_env")

        if contest_env_dir.exists():
            # contest_envが存在する場合の構造確認
            assert contest_env_dir.is_dir(), "contest_envがディレクトリではありません"

            # 基本的な言語ディレクトリの確認
            expected_languages = ["python", "cpp", "rust"]
            for language in expected_languages:
                lang_dir = contest_env_dir / language
                if lang_dir.exists():
                    assert lang_dir.is_dir(), f"{language}ディレクトリが正しくありません"



class TestConfigValuesAccess:
    """設定値アクセスのテスト"""

    def test_docker_defaults_access(self):
        """docker_defaults設定へのアクセステスト"""
        import json

        docker_config_path = Path("config/system/docker_defaults.json")
        if docker_config_path.exists():
            with open(docker_config_path, encoding='utf-8') as f:
                docker_config = json.load(f)

            # 基本的な設定の存在確認
            assert "docker_defaults" in docker_config
            docker_defaults = docker_config["docker_defaults"]

            # 重要な設定項目の確認
            expected_keys = [
                "docker_workspace_mount_path",
                "docker_working_directory",
                "docker_options"
            ]

            for key in expected_keys:
                assert key in docker_defaults, f"docker_defaults.{key} が見つかりません"

    def test_dev_config_access(self):
        """dev_config設定へのアクセステスト"""
        import json

        dev_config_path = Path("config/system/dev_config.json")
        if dev_config_path.exists():
            with open(dev_config_path, encoding='utf-8') as f:
                dev_config = json.load(f)

            # 基本的な設定の存在確認
            assert "dev_config" in dev_config
            dev_settings = dev_config["dev_config"]

            # デバッグ設定の確認
            if "debug" in dev_settings:
                debug_config = dev_settings["debug"]
                assert isinstance(debug_config.get("enabled", False), bool)


class TestConfigSystemIntegration:
    """設定システム統合テスト"""

    @patch('src.cli.cli_app.parse_user_input')
    @patch('src.cli.cli_app.WorkflowExecutionService')
    def test_full_config_integration(self, mock_service_class, mock_parse):
        """完全な設定統合テスト"""
        # 実際の設定システムを使用してCLI実行をテスト
        mock_logger = MagicMock()
        mock_infrastructure = MagicMock()

        # 実際の設定解析をシミュレート
        mock_context = MagicMock()
        mock_context.language = "python"
        mock_context.command_type = "test"
        mock_context.contest_name = "abc301"
        mock_context.problem_name = "a"
        mock_context.env_type = "local"

        mock_parse.return_value = mock_context

        mock_service = MagicMock()
        mock_service.execute_workflow.return_value = WorkflowExecutionResult(
            success=True, results=[], preparation_results=[], errors=[], warnings=[]
        )
        mock_service_class.return_value = mock_service

        # CLI実行
        app = MinimalCLIApp(infrastructure=mock_infrastructure, logger=mock_logger)
        result = app.run_cli_application(["python", "test", "abc301", "a"])

        # 成功することを確認
        assert result == 0

        # 設定システムが統合されていることを確認
        mock_parse.assert_called_once()
        mock_service_class.assert_called_once()
        mock_service.execute_workflow.assert_called_once()
