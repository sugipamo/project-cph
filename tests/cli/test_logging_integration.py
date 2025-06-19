"""ログ統合のテスト"""
from unittest.mock import MagicMock, patch

import pytest

from src.cli.cli_app import MinimalCLIApp
from src.operations.exceptions.composite_step_failure import CompositeStepFailureError
from src.operations.exceptions.error_codes import ErrorCode
from src.workflow.workflow_result import WorkflowExecutionResult


class TestLoggingIntegration:
    """ログシステム統合のテスト"""

    @patch('src.cli.cli_app.parse_user_input')
    @patch('src.cli.cli_app.WorkflowExecutionService')
    def test_logger_injection_and_usage(self, mock_service_class, mock_parse):
        """ログ注入と使用のテスト"""
        # モックのセットアップ
        mock_logger = MagicMock()
        mock_infrastructure = MagicMock()
        mock_context = MagicMock()
        mock_service = MagicMock()
        mock_result = WorkflowExecutionResult(
            success=True, results=[], preparation_results=[], errors=[], warnings=[]
        )

        mock_parse.return_value = mock_context
        mock_service_class.return_value = mock_service
        mock_service.execute_workflow.return_value = mock_result

        # テスト実行（インフラとログを注入）
        app = MinimalCLIApp(infrastructure=mock_infrastructure, logger=mock_logger)
        result = app.run_cli_application(["python", "test", "abc301", "a"])

        # ログ注入の確認
        assert app.logger is mock_logger

        # ログメソッドが呼ばれることの確認
        mock_logger.info.assert_any_call("CLI実行開始: python test abc301 a")
        mock_logger.info.assert_any_call("CLI実行完了")

        # 戻り値の確認
        assert result == 0

    @patch('src.cli.cli_app.build_infrastructure')
    @patch('src.cli.cli_app.parse_user_input')
    @patch('src.cli.cli_app.WorkflowExecutionService')
    def test_workflow_failure_logging(self, mock_service_class, mock_parse, mock_build_infra):
        """ワークフロー失敗時のログテスト"""
        # モックのセットアップ
        mock_logger = MagicMock()
        mock_infrastructure = MagicMock()
        mock_infrastructure.resolve.return_value = mock_logger
        mock_context = MagicMock()
        mock_service = MagicMock()
        mock_result = WorkflowExecutionResult(
            success=False, results=[], preparation_results=[],
            errors=["テストエラー"], warnings=["テスト警告"]
        )

        mock_build_infra.return_value = mock_infrastructure
        mock_parse.return_value = mock_context
        mock_service_class.return_value = mock_service
        mock_service.execute_workflow.return_value = mock_result

        # テスト実行
        app = MinimalCLIApp()
        result = app.run_cli_application(["python", "test", "abc301", "a"])

        # 失敗ログの確認
        mock_logger.error.assert_any_call("CLI実行失敗")
        mock_logger.error.assert_any_call("ワークフローエラー: テストエラー")
        mock_logger.warning.assert_any_call("ワークフロー警告: テスト警告")

        assert result == 1

    def test_composite_error_logging_with_logger(self):
        """CompositeStepFailureErrorのログ出力テスト"""
        mock_logger = MagicMock()
        app = MinimalCLIApp(logger=mock_logger)

        # CompositeStepFailureErrorを作成
        composite_error = CompositeStepFailureError(
            "ステップ実行失敗",
            error_code=ErrorCode.FILE_NOT_FOUND
        )

        # エラー処理の実行
        result = app._handle_composite_step_failure(composite_error)

        # ログが呼ばれることの確認
        mock_logger.error.assert_any_call("CompositeStepFailure: ステップ実行失敗")
        mock_logger.error.assert_any_call("🚨 実行エラーが発生しました")

        assert result == 1

    def test_composite_error_requires_logger(self):
        """loggerが必須であることのテスト"""
        app = MinimalCLIApp()
        # loggerを設定しない（None状態）

        composite_error = CompositeStepFailureError(
            "ステップ実行失敗",
            error_code=ErrorCode.FILE_NOT_FOUND
        )

        # loggerがNoneの場合はAttributeErrorが発生することを確認
        with pytest.raises(AttributeError):
            app._handle_composite_step_failure(composite_error)

    def test_general_exception_logging_with_logger(self):
        """一般例外のログ出力テスト"""
        mock_logger = MagicMock()
        app = MinimalCLIApp(logger=mock_logger)

        # 一般例外を作成
        exception = ValueError("無効な値")
        args = ["python", "test", "abc301", "a"]

        # エラー処理の実行
        result = app._handle_general_exception(exception, args)

        # ログが呼ばれることの確認
        mock_logger.error.assert_any_call("一般例外: 無効な値")
        mock_logger.error.assert_any_call("🚨 予期せぬエラーが発生しました")

        assert result == 1

    def test_debug_mode_logging(self):
        """デバッグモードでのログ出力テスト"""
        mock_logger = MagicMock()
        app = MinimalCLIApp(logger=mock_logger)

        exception = RuntimeError("テストエラー")
        args = ["python", "test", "abc301", "a", "--debug"]

        # エラー処理の実行
        result = app._handle_general_exception(exception, args)

        # デバッグログが呼ばれることの確認
        mock_logger.debug.assert_any_call("デバッグ情報:")
        # スタックトレースのログも確認
        debug_calls = [call for call in mock_logger.debug.call_args_list
                      if "スタックトレース:" in str(call)]
        assert len(debug_calls) > 0

        assert result == 1

    @patch('src.cli.cli_app.build_infrastructure')
    def test_automatic_logger_resolution(self, mock_build_infra):
        """自動ログ解決のテスト"""
        # インフラストラクチャ構築の正常ケース
        mock_logger = MagicMock()
        mock_infrastructure = MagicMock()
        mock_infrastructure.resolve.return_value = mock_logger
        mock_build_infra.return_value = mock_infrastructure

        app = MinimalCLIApp()

        # ログが設定されていないことを確認
        assert app.logger is None
        assert app.infrastructure is None

        # runを呼ばずに、個別にテスト
        # infrastructure初期化をテストするため、簡単な例外を発生させる
        with patch('src.cli.cli_app.parse_user_input') as mock_parse:
            mock_parse.side_effect = Exception("テスト例外")

            result = app.run_cli_application(["test"])

            # インフラストラクチャとログが自動設定されることを確認
            assert app.infrastructure is mock_infrastructure
            assert app.logger is mock_logger
            assert result == 1


class TestLoggingBestPractices:
    """ログのベストプラクティステスト"""

    def test_no_print_statements_used(self):
        """printが使用されないことを確認"""
        mock_logger = MagicMock()
        app = MinimalCLIApp(logger=mock_logger)

        # 成功結果のテスト
        success_result = WorkflowExecutionResult(
            success=True, results=[], preparation_results=[], errors=[], warnings=[]
        )

        # print呼び出しをキャプチャ
        with patch('builtins.print') as mock_print:
            app._present_results(success_result)
            # printが呼ばれないことを確認
            mock_print.assert_not_called()

    def test_logger_only_used(self):
        """ログのみが使用されることを確認"""
        mock_logger = MagicMock()
        app = MinimalCLIApp(logger=mock_logger)

        # エラー結果のテスト
        error_result = WorkflowExecutionResult(
            success=False, results=[], preparation_results=[],
            errors=["テストエラー"], warnings=["テスト警告"]
        )

        with patch('builtins.print') as mock_print:
            app._present_results(error_result)

            # ログが使用されることを確認
            mock_logger.error.assert_called()
            mock_logger.warning.assert_called()

            # printが呼ばれないことを確認
            mock_print.assert_not_called()

    def test_structured_error_logging(self):
        """構造化されたエラーログの確認"""
        mock_logger = MagicMock()
        app = MinimalCLIApp(logger=mock_logger)

        composite_error = CompositeStepFailureError(
            "構造化テストエラー",
            error_code=ErrorCode.DOCKER_NOT_AVAILABLE
        )

        app._handle_composite_step_failure(composite_error)

        # 構造化されたログメッセージの確認
        error_calls = mock_logger.error.call_args_list
        error_messages = [str(call) for call in error_calls]

        # エラー境界の確認
        assert any("=" * 60 in msg for msg in error_messages)
        # エラーコードを含むメッセージの確認
        assert any("DOCKER_NOT_AVAILABLE" in msg for msg in error_messages)


class TestDependencyInjection:
    """依存性注入のテスト"""

    def test_infrastructure_injection(self):
        """インフラストラクチャ注入のテスト"""
        mock_infrastructure = MagicMock()
        app = MinimalCLIApp(infrastructure=mock_infrastructure)

        assert app.infrastructure is mock_infrastructure

    def test_logger_injection(self):
        """ログ注入のテスト"""
        mock_logger = MagicMock()
        app = MinimalCLIApp(logger=mock_logger)

        assert app.logger is mock_logger

    def test_both_injection(self):
        """両方注入のテスト"""
        mock_infrastructure = MagicMock()
        mock_logger = MagicMock()
        app = MinimalCLIApp(infrastructure=mock_infrastructure, logger=mock_logger)

        assert app.infrastructure is mock_infrastructure
        assert app.logger is mock_logger
