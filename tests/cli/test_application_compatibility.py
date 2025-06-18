"""既存applicationとの互換性確認テスト"""
from unittest.mock import MagicMock, patch

import pytest

from src.application.cli_application import CLIApplication
from src.cli.cli_app import MinimalCLIApp
from src.workflow.workflow_result import WorkflowExecutionResult


class TestApplicationCompatibility:
    """既存CLIApplicationとMinimalCLIAppの互換性テスト"""

    def setup_common_mocks(self):
        """共通のモックセットアップ"""
        mock_infrastructure = MagicMock()
        mock_context = MagicMock()
        mock_context.env_json = {
            "python": {
                "commands": {
                    "test": {
                        "steps": [],
                        "parallel": {"enabled": False, "max_workers": 4}
                    }
                }
            },
            "shared": {
                "environment_logging": {"enabled": False}
            }
        }
        mock_result = WorkflowExecutionResult(
            success=True,
            results=[],
            preparation_results=[],
            errors=[],
            warnings=[]
        )
        return mock_infrastructure, mock_context, mock_result

    @patch('src.cli.cli_app.build_infrastructure')
    @patch('src.cli.cli_app.parse_user_input')
    @patch('src.cli.cli_app.WorkflowExecutionService')
    @patch('src.application.cli_application.build_infrastructure')
    @patch('src.application.cli_application.parse_user_input')
    @patch('src.application.cli_application.WorkflowExecutionService')
    def test_same_arguments_same_behavior(self, old_workflow_service, old_parse, old_build,
                                        new_workflow_service, new_parse, new_build):
        """同じ引数で同じ動作をすることを確認"""
        mock_infrastructure, mock_context, mock_result = self.setup_common_mocks()

        # 既存アプリケーションのモック設定
        old_build.return_value = mock_infrastructure
        old_parse.return_value = mock_context
        old_service = MagicMock()
        old_service.execute_workflow.return_value = mock_result
        old_workflow_service.return_value = old_service

        # 新CLIアプリケーションのモック設定
        new_build.return_value = mock_infrastructure
        new_parse.return_value = mock_context
        new_service = MagicMock()
        new_service.execute_workflow.return_value = mock_result
        new_workflow_service.return_value = new_service

        # 同じ引数でテスト
        test_args = ["python", "test", "abc301", "a"]

        # 既存アプリケーションの実行
        old_app = CLIApplication()
        old_result = old_app.execute_cli_application(test_args)

        # 新CLIアプリケーションの実行
        new_app = MinimalCLIApp()
        new_result = new_app.run(test_args)

        # 結果が同じことを確認
        assert old_result == new_result == 0

        # 同じサービスが呼ばれることを確認
        old_parse.assert_called_once_with(test_args, mock_infrastructure)
        new_parse.assert_called_once_with(test_args, mock_infrastructure)

    @patch('src.cli.cli_app.build_infrastructure')
    @patch('src.cli.cli_app.parse_user_input')
    @patch('src.application.cli_application.build_infrastructure')
    @patch('src.application.cli_application.parse_user_input')
    def test_error_handling_compatibility(self, old_parse, old_build, new_parse, new_build):
        """エラーハンドリングの互換性確認"""
        # エラーケースのテスト
        old_build.side_effect = Exception("テストエラー")
        new_build.side_effect = Exception("テストエラー")

        # 既存アプリケーションのエラー処理
        old_app = CLIApplication()
        old_result = old_app.execute_cli_application(["test"])

        # 新CLIアプリケーションのエラー処理
        new_app = MinimalCLIApp()
        new_result = new_app.run(["test"])

        # 両方ともエラーコード1を返すことを確認
        assert old_result == new_result == 1

    def test_interface_compatibility(self):
        """インターフェースの互換性確認"""
        old_app = CLIApplication()
        new_app = MinimalCLIApp()

        # 必要なメソッドが存在することを確認
        assert hasattr(old_app, 'execute_cli_application')
        assert hasattr(new_app, 'run')

        # メソッドが呼び出し可能であることを確認
        assert callable(old_app.execute_cli_application)
        assert callable(new_app.run)

    @patch('src.cli.cli_app.build_infrastructure')
    @patch('src.cli.cli_app.parse_user_input')
    @patch('src.cli.cli_app.WorkflowExecutionService')
    def test_di_container_usage_consistency(self, mock_workflow_service, mock_parse, mock_build):
        """DIコンテナ使用の一貫性確認"""
        mock_infrastructure, mock_context, mock_result = self.setup_common_mocks()

        mock_build.return_value = mock_infrastructure
        mock_parse.return_value = mock_context
        mock_service = MagicMock()
        mock_service.execute_workflow.return_value = mock_result
        mock_workflow_service.return_value = mock_service

        # 新CLIアプリケーションでDIコンテナが正しく使用されることを確認
        new_app = MinimalCLIApp()
        new_app.run(["python", "test", "abc301", "a"])

        # build_infrastructureが呼ばれることを確認
        mock_build.assert_called_once()

        # インフラストラクチャがparse_user_inputに渡されることを確認
        mock_parse.assert_called_once_with(["python", "test", "abc301", "a"], mock_infrastructure)

        # WorkflowExecutionServiceにコンテキストとインフラが渡されることを確認
        mock_workflow_service.assert_called_once_with(mock_context, mock_infrastructure)


class TestBackwardCompatibility:
    """後方互換性のテスト"""

    @patch('src.cli.cli_app.build_infrastructure')
    @patch('src.cli.cli_app.parse_user_input')
    @patch('src.cli.cli_app.WorkflowExecutionService')
    def test_minimal_cli_replaces_full_cli(self, mock_workflow_service, mock_parse, mock_build):
        """MinimalCLIAppが既存CLIApplicationの代替として機能することを確認"""
        mock_infrastructure = MagicMock()
        mock_context = MagicMock()
        mock_result = WorkflowExecutionResult(
            success=True,
            results=[],
            preparation_results=[],
            errors=[],
            warnings=[]
        )

        mock_build.return_value = mock_infrastructure
        mock_parse.return_value = mock_context
        mock_service = MagicMock()
        mock_service.execute_workflow.return_value = mock_result
        mock_workflow_service.return_value = mock_service

        # 基本的なワークフローが実行できることを確認
        app = MinimalCLIApp()
        result = app.run(["python", "test", "abc301", "a"])

        # 成功することを確認
        assert result == 0

        # 必要な処理が実行されることを確認
        assert mock_build.called
        assert mock_parse.called
        assert mock_workflow_service.called
        assert mock_service.execute_workflow.called

    def test_minimal_features_sufficient(self):
        """最小限の機能で十分であることを確認"""
        app = MinimalCLIApp()

        # 必要最小限の属性とメソッドが存在することを確認
        required_attributes = ['infrastructure', 'context']
        required_methods = ['run', '_execute_workflow', '_present_results']

        for attr in required_attributes:
            assert hasattr(app, attr), f"必要な属性 {attr} が存在しません"

        for method in required_methods:
            assert hasattr(app, method), f"必要なメソッド {method} が存在しません"
            assert callable(getattr(app, method)), f"メソッド {method} が呼び出し可能ではありません"


class TestMigrationPath:
    """移行パスのテスト"""

    def test_can_import_both_applications(self):
        """両方のアプリケーションがインポートできることを確認"""
        # インポートエラーが発生しないことを確認
        from src.application.cli_application import CLIApplication
        from src.cli.cli_app import MinimalCLIApp

        # インスタンス化できることを確認
        old_app = CLIApplication()
        new_app = MinimalCLIApp()

        assert isinstance(old_app, CLIApplication)
        assert isinstance(new_app, MinimalCLIApp)

    @patch('src.cli.cli_app.build_infrastructure')
    @patch('src.cli.cli_app.parse_user_input')
    def test_minimal_cli_entry_point(self, mock_parse, mock_build):
        """MinimalCLIAppがエントリーポイントとして機能することを確認"""
        mock_infrastructure = MagicMock()
        mock_context = MagicMock()

        mock_build.return_value = mock_infrastructure
        mock_parse.return_value = mock_context

        # main関数相当の動作ができることを確認
        app = MinimalCLIApp()

        with patch.object(app, '_execute_workflow') as mock_execute:
            mock_execute.return_value = MagicMock(success=True, errors=[], warnings=[])

            # CLIとして実行できることを確認
            result = app.run(["python", "test", "abc301", "a"])
            assert result == 0
