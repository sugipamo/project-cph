"""CLI アプリケーションの統合テスト"""
from unittest.mock import MagicMock, patch

import pytest

from src.cli.cli_app import MinimalCLIApp
from src.workflow.workflow_result import WorkflowExecutionResult


class TestMinimalCLIApp:
    """MinimalCLIAppの統合テスト"""

    def test_init(self):
        """初期化テスト"""
        app = MinimalCLIApp()
        assert app.infrastructure is None
        assert app.context is None

    @patch('src.cli.cli_app.build_infrastructure')
    @patch('src.cli.cli_app.parse_user_input')
    @patch('src.cli.cli_app.WorkflowExecutionService')
    def test_run_success(self, mock_service_class, mock_parse_input, mock_build_infra):
        """正常実行のテスト"""
        # モックセットアップ
        mock_infrastructure = MagicMock()
        mock_context = MagicMock()
        mock_service = MagicMock()
        mock_result = WorkflowExecutionResult(
            success=True,
            results=[],
            preparation_results=[],
            errors=[],
            warnings=[]
        )

        mock_build_infra.return_value = mock_infrastructure
        mock_parse_input.return_value = mock_context
        mock_service_class.return_value = mock_service
        mock_service.execute_workflow.return_value = mock_result

        # テスト実行
        app = MinimalCLIApp()
        result = app.run_cli_application(["python", "test", "abc301", "a"])

        # アサーション
        assert result == 0
        mock_build_infra.assert_called_once()
        mock_parse_input.assert_called_once_with(["python", "test", "abc301", "a"], mock_infrastructure)
        mock_service_class.assert_called_once_with(mock_context, mock_infrastructure)
        mock_service.execute_workflow.assert_called_once()

    @patch('src.cli.cli_app.build_infrastructure')
    @patch('src.cli.cli_app.parse_user_input')
    @patch('src.cli.cli_app.WorkflowExecutionService')
    def test_run_workflow_failure(self, mock_service_class, mock_parse_input, mock_build_infra):
        """ワークフロー実行失敗のテスト"""
        # モックセットアップ
        mock_infrastructure = MagicMock()
        mock_context = MagicMock()
        mock_service = MagicMock()
        mock_result = WorkflowExecutionResult(
            success=False,
            results=[],
            preparation_results=[],
            errors=["テストエラー"],
            warnings=[]
        )

        mock_build_infra.return_value = mock_infrastructure
        mock_parse_input.return_value = mock_context
        mock_service_class.return_value = mock_service
        mock_service.execute_workflow.return_value = mock_result

        # テスト実行
        app = MinimalCLIApp()
        result = app.run_cli_application(["python", "test", "abc301", "a"])

        # アサーション
        assert result == 1

    @patch('src.cli.cli_app.build_infrastructure')
    def test_run_infrastructure_failure(self, mock_build_infra):
        """インフラストラクチャ初期化失敗のテスト"""
        # モックセットアップ
        mock_build_infra.side_effect = Exception("インフラストラクチャエラー")

        # テスト実行
        app = MinimalCLIApp()

        # アサーション - 明示的な例外が発生することを期待
        with pytest.raises(RuntimeError, match="Infrastructure initialization failed"):
            app.run_cli_application(["python", "test", "abc301", "a"])

    @patch('src.cli.cli_app.build_infrastructure')
    @patch('src.cli.cli_app.parse_user_input')
    def test_run_parse_failure(self, mock_parse_input, mock_build_infra):
        """入力解析失敗のテスト"""
        # モックセットアップ
        mock_infrastructure = MagicMock()
        mock_build_infra.return_value = mock_infrastructure
        mock_parse_input.side_effect = ValueError("解析エラー")

        # テスト実行
        app = MinimalCLIApp()
        result = app.run_cli_application(["invalid", "args"])

        # アサーション
        assert result == 1

    def test_present_results_with_errors(self):
        """エラー結果の表示テスト"""
        # モックロガーを設定
        mock_logger = MagicMock()
        app = MinimalCLIApp(logger=mock_logger)
        result = WorkflowExecutionResult(
            success=False,
            results=[],
            preparation_results=[],
            errors=["エラー1", "エラー2"],
            warnings=["警告1"]
        )

        # テスト実行
        app._present_results(result)

        # ロガーの呼び出し確認
        assert mock_logger.error.called
        assert mock_logger.warning.called

        error_calls = [call.args[0] for call in mock_logger.error.call_args_list]
        warning_calls = [call.args[0] for call in mock_logger.warning.call_args_list]

        assert "ワークフローエラー: エラー1" in error_calls
        assert "ワークフローエラー: エラー2" in error_calls
        assert "ワークフロー警告: 警告1" in warning_calls

    def test_present_results_success(self, capsys):
        """成功結果の表示テスト"""
        app = MinimalCLIApp()
        result = WorkflowExecutionResult(
            success=True,
            results=[],
            preparation_results=[],
            errors=[],
            warnings=[]
        )

        # テスト実行
        app._present_results(result)

        # 出力確認（何も出力されないことを確認）
        captured = capsys.readouterr()
        assert captured.out == ""


