"""CLI機能の詳細テスト - DI注入とワークフロー構築の検証"""
from unittest.mock import MagicMock, patch

import pytest

from src.cli.cli_app import MinimalCLIApp
from src.infrastructure.di_container import DIContainer, DIKey


class TestCLIDIInjection:
    """DI注入機能のテスト"""

    @patch('src.cli.cli_app.build_infrastructure')
    def test_di_container_injection(self, mock_build_infra):
        """DIコンテナが正しく注入されることを確認"""
        # モックDIコンテナをセットアップ
        mock_container = MagicMock(spec=DIContainer)
        mock_build_infra.return_value = mock_container

        # CLI初期化時にDIコンテナが設定されることを確認
        app = MinimalCLIApp()
        with patch('src.cli.cli_app.parse_user_input') as mock_parse:
            mock_parse.return_value = MagicMock()
            with patch.object(app, '_execute_workflow') as mock_execute:
                mock_execute.return_value = MagicMock(success=True, errors=[], warnings=[])

                app.run_cli_application(["test"])

                # DIコンテナが正しく設定されていることを確認
                assert app.infrastructure is mock_container
                mock_build_infra.assert_called_once()

    @patch('src.cli.cli_app.build_infrastructure')
    @patch('src.cli.cli_app.parse_user_input')
    def test_infrastructure_passed_to_parser(self, mock_parse, mock_build_infra):
        """インフラストラクチャがパーサーに渡されることを確認"""
        mock_container = MagicMock()
        mock_build_infra.return_value = mock_container
        mock_parse.return_value = MagicMock()

        app = MinimalCLIApp()
        with patch.object(app, '_execute_workflow') as mock_execute:
            mock_execute.return_value = MagicMock(success=True, errors=[], warnings=[])

            args = ["python", "test", "abc301", "a"]
            app.run_cli_application(args)

            # parse_user_inputにインフラストラクチャが渡されることを確認
            mock_parse.assert_called_once_with(args, mock_container)


class TestCLIWorkflowConstruction:
    """ワークフロー構築機能のテスト"""

    @patch('src.cli.cli_app.build_infrastructure')
    @patch('src.cli.cli_app.parse_user_input')
    @patch('src.cli.cli_app.WorkflowExecutionService')
    def test_workflow_service_creation(self, mock_service_class, mock_parse, mock_build_infra):
        """WorkflowExecutionServiceが正しく作成されることを確認"""
        mock_container = MagicMock()
        mock_context = MagicMock()
        mock_service = MagicMock()

        mock_build_infra.return_value = mock_container
        mock_parse.return_value = mock_context
        mock_service_class.return_value = mock_service
        mock_service.execute_workflow.return_value = MagicMock(success=True, errors=[], warnings=[])

        app = MinimalCLIApp()
        app.run_cli_application(["test"])

        # WorkflowExecutionServiceがコンテキストとインフラで作成されることを確認
        mock_service_class.assert_called_once_with(mock_context, mock_container)

    @patch('src.cli.cli_app.build_infrastructure')
    @patch('src.cli.cli_app.parse_user_input')
    @patch('src.cli.cli_app.WorkflowExecutionService')
    def test_workflow_execution(self, mock_service_class, mock_parse, mock_build_infra):
        """ワークフローが正しく実行されることを確認"""
        mock_container = MagicMock()
        mock_context = MagicMock()
        mock_service = MagicMock()
        mock_result = MagicMock(success=True, errors=[], warnings=[])

        mock_build_infra.return_value = mock_container
        mock_parse.return_value = mock_context
        mock_service_class.return_value = mock_service
        mock_service.execute_workflow.return_value = mock_result

        app = MinimalCLIApp()
        result = app.run_cli_application(["test"])

        # ワークフローが実行されることを確認
        mock_service.execute_workflow.assert_called_once()
        assert result == 0  # 成功時は0を返す


class TestCLIErrorHandling:
    """CLI エラーハンドリングのテスト"""

    @patch('src.cli.cli_app.build_infrastructure')
    def test_infrastructure_build_error(self, mock_build_infra):
        """インフラストラクチャ構築エラーの処理"""
        mock_build_infra.side_effect = Exception("DI初期化エラー")

        app = MinimalCLIApp()

        # 明示的な例外が発生することを期待
        with pytest.raises(RuntimeError, match="Infrastructure initialization failed"):
            app.run_cli_application(["test"])

    @patch('src.cli.cli_app.build_infrastructure')
    @patch('src.cli.cli_app.parse_user_input')
    def test_context_parse_error(self, mock_parse, mock_build_infra):
        """コンテキスト解析エラーの処理"""
        mock_build_infra.return_value = MagicMock()
        mock_parse.side_effect = ValueError("引数解析エラー")

        app = MinimalCLIApp()
        result = app.run_cli_application(["invalid"])

        assert result == 1  # エラー時は1を返す

    @patch('src.cli.cli_app.build_infrastructure')
    @patch('src.cli.cli_app.parse_user_input')
    @patch('src.cli.cli_app.WorkflowExecutionService')
    def test_workflow_execution_error(self, mock_service_class, mock_parse, mock_build_infra):
        """ワークフロー実行エラーの処理"""
        mock_build_infra.return_value = MagicMock()
        mock_parse.return_value = MagicMock()
        mock_service = MagicMock()
        mock_service.execute_workflow.side_effect = Exception("ワークフロー実行エラー")
        mock_service_class.return_value = mock_service

        app = MinimalCLIApp()
        result = app.run_cli_application(["test"])

        assert result == 1  # エラー時は1を返す


class TestCLIMinimalFeatures:
    """CLIの最小限機能テスト"""

    def test_minimal_cli_has_required_methods(self):
        """必要なメソッドが実装されていることを確認"""
        app = MinimalCLIApp()

        # 必要なメソッドの存在確認
        assert hasattr(app, 'run_cli_application')
        assert hasattr(app, '_execute_workflow')
        assert hasattr(app, '_present_results')
        assert callable(app.run_cli_application)
        assert callable(app._execute_workflow)
        assert callable(app._present_results)

    def test_minimal_cli_attributes(self):
        """必要な属性が初期化されていることを確認"""
        app = MinimalCLIApp()

        # 必要な属性の存在確認
        assert hasattr(app, 'infrastructure')
        assert hasattr(app, 'context')

        # 初期状態の確認
        assert app.infrastructure is None
        assert app.context is None
