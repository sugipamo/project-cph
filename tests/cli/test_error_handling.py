"""エラーハンドリング強化のテスト"""
import sys
from io import StringIO
from unittest.mock import MagicMock, patch

import pytest

from src.cli.cli_app import MinimalCLIApp
from src.operations.exceptions.composite_step_failure import CompositeStepFailureError
from src.operations.exceptions.error_codes import ErrorCode
from src.workflow.workflow_result import WorkflowExecutionResult


class TestEnhancedErrorHandling:
    """強化されたエラーハンドリングのテスト"""

    def test_composite_step_failure_handling(self, capsys):
        """CompositeStepFailureErrorの処理テスト"""
        # モックロガーを設定
        mock_logger = MagicMock()
        app = MinimalCLIApp(logger=mock_logger)

        # モックの結果オブジェクト
        mock_result = MagicMock()
        mock_result.get_error_output.return_value = "詳細なエラー出力"

        # CompositeStepFailureErrorを作成
        original_exception = FileNotFoundError("テストファイルが見つかりません")
        composite_error = CompositeStepFailureError(
            "ステップ実行に失敗しました",
            result=mock_result,
            original_exception=original_exception,
            error_code=ErrorCode.FILE_NOT_FOUND
        )

        # エラーハンドリングのテスト
        result = app._handle_composite_step_failure(composite_error)

        # 戻り値の確認
        assert result == 1

        # ロガーの呼び出し確認
        assert mock_logger.error.called
        error_calls = [call.args[0] for call in mock_logger.error.call_args_list]
        error_output = " ".join(error_calls)

        assert "🚨 実行エラーが発生しました" in error_output
        assert "FILE_NOT_FOUND" in error_output
        assert "詳細なエラー出力" in error_output
        assert "FileNotFoundError" in error_output

    def test_general_exception_handling(self):
        """一般的な例外の処理テスト"""
        # モックロガーを設定
        mock_logger = MagicMock()
        app = MinimalCLIApp(logger=mock_logger)

        # 一般的な例外を作成
        exception = ValueError("無効な引数です")
        args = ["python", "test", "abc301", "a"]

        # エラーハンドリングのテスト
        result = app._handle_general_exception(exception, args)

        # 戻り値の確認
        assert result == 1

        # ロガーの呼び出し確認
        assert mock_logger.error.called
        error_calls = [call.args[0] for call in mock_logger.error.call_args_list]
        error_output = " ".join(error_calls)

        assert "🚨 予期せぬエラーが発生しました" in error_output
        assert "無効な引数です" in error_output
        assert "分類:" in error_output
        assert "提案:" in error_output

    def test_debug_mode_traceback(self):
        """デバッグモードでのトレースバック表示テスト"""
        # モックロガーを設定
        mock_logger = MagicMock()
        app = MinimalCLIApp(logger=mock_logger)

        exception = RuntimeError("テストエラー")
        args = ["python", "test", "abc301", "a", "--debug"]

        # エラーハンドリングのテスト
        result = app._handle_general_exception(exception, args)

        # 戻り値の確認
        assert result == 1

        # デバッグ情報が出力されることを確認
        assert mock_logger.debug.called
        debug_calls = [call.args[0] for call in mock_logger.debug.call_args_list]
        debug_output = " ".join(debug_calls)
        assert "デバッグ情報:" in debug_output

    def test_error_classification(self):
        """エラー分類の動作テスト"""
        # モックロガーを設定
        mock_logger = MagicMock()
        app = MinimalCLIApp(logger=mock_logger)

        # ファイル関連エラー
        file_error = FileNotFoundError("ファイルが見つかりません")
        app._handle_general_exception(file_error, [])

        # ロガーの呼び出し確認
        assert mock_logger.error.called
        error_calls = [call.args[0] for call in mock_logger.error.call_args_list]
        error_output = " ".join(error_calls)
        assert "FILE_NOT_FOUND" in error_output
        assert "Check if the file path exists" in error_output

    @patch('src.cli.cli_app.build_infrastructure')
    def test_infrastructure_error_handling(self, mock_build_infra):
        """インフラストラクチャエラーのハンドリングテスト"""
        # インフラストラクチャ構築でエラー発生
        mock_build_infra.side_effect = Exception("DI初期化エラー")

        app = MinimalCLIApp()
        result = app.run(["test"])

        # エラーが適切に処理されることを確認
        assert result == 1

    @patch('src.cli.cli_app.build_infrastructure')
    @patch('src.cli.cli_app.parse_user_input')
    def test_parse_error_handling(self, mock_parse, mock_build_infra):
        """入力解析エラーのハンドリングテスト"""
        mock_build_infra.return_value = MagicMock()
        mock_parse.side_effect = ValueError("無効な引数")

        app = MinimalCLIApp()
        result = app.run(["invalid"])

        # エラーが適切に処理されることを確認
        assert result == 1


class TestErrorHandlingIntegration:
    """エラーハンドリングの統合テスト"""

    @patch('src.cli.cli_app.build_infrastructure')
    @patch('src.cli.cli_app.parse_user_input')
    @patch('src.cli.cli_app.WorkflowExecutionService')
    def test_workflow_composite_error_propagation(self, mock_service_class, mock_parse, mock_build_infra):
        """ワークフローからのCompositeStepFailureError伝播テスト"""
        mock_infrastructure = MagicMock()
        mock_context = MagicMock()
        mock_service = MagicMock()

        # CompositeStepFailureErrorを発生させる
        composite_error = CompositeStepFailureError(
            "ワークフロー実行失敗",
            error_code=ErrorCode.WORKFLOW_STEP_FAILED
        )
        mock_service.execute_workflow.side_effect = composite_error

        mock_build_infra.return_value = mock_infrastructure
        mock_parse.return_value = mock_context
        mock_service_class.return_value = mock_service

        # テスト実行
        app = MinimalCLIApp()
        with patch.object(app, '_handle_composite_step_failure') as mock_handle:
            mock_handle.return_value = 1

            result = app.run(["test"])

            # CompositeStepFailureErrorが適切に処理されることを確認
            assert result == 1
            mock_handle.assert_called_once_with(composite_error)

    @patch('src.cli.cli_app.build_infrastructure')
    @patch('src.cli.cli_app.parse_user_input')
    @patch('src.cli.cli_app.WorkflowExecutionService')
    def test_workflow_failure_result_handling(self, mock_service_class, mock_parse, mock_build_infra):
        """ワークフロー実行失敗結果の処理テスト"""
        # モックロガーを設定
        mock_logger = MagicMock()
        mock_infrastructure = MagicMock()
        mock_infrastructure.resolve.return_value = mock_logger
        mock_context = MagicMock()
        mock_service = MagicMock()

        # 失敗結果を返すワークフロー
        failed_result = WorkflowExecutionResult(
            success=False,
            results=[],
            preparation_results=[],
            errors=["ステップ1が失敗しました", "ステップ2が失敗しました"],
            warnings=["警告: リソース不足"]
        )
        mock_service.execute_workflow.return_value = failed_result

        mock_build_infra.return_value = mock_infrastructure
        mock_parse.return_value = mock_context
        mock_service_class.return_value = mock_service

        # テスト実行
        app = MinimalCLIApp()
        result = app.run(["test"])

        # 失敗コードを返すことを確認
        assert result == 1

        # エラーと警告がロガーに送られることを確認
        assert mock_logger.error.called
        assert mock_logger.warning.called


class TestErrorRecoveryActions:
    """エラー回復手順のテスト"""

    def test_recovery_actions_display(self):
        """回復手順の表示テスト"""
        # モックロガーを設定
        mock_logger = MagicMock()
        app = MinimalCLIApp(logger=mock_logger)

        # ファイル未発見エラー（回復手順あり）
        file_error = FileNotFoundError("ファイルが見つかりません")
        app._handle_general_exception(file_error, [])

        # ロガーの呼び出し確認
        assert mock_logger.error.called
        error_calls = [call.args[0] for call in mock_logger.error.call_args_list]
        error_output = " ".join(error_calls)
        assert "回復手順:" in error_output
        assert "1. Verify the file path is correct" in error_output
        assert "2. Check if the file was moved or deleted" in error_output

    def test_no_recovery_actions_for_unknown_error(self):
        """不明エラーの回復手順表示テスト"""
        # モックロガーを設定
        mock_logger = MagicMock()
        app = MinimalCLIApp(logger=mock_logger)

        # 分類できないエラー
        unknown_error = Exception("不明なエラー")
        app._handle_general_exception(unknown_error, [])

        # ロガーの呼び出し確認
        assert mock_logger.error.called
        error_calls = [call.args[0] for call in mock_logger.error.call_args_list]
        error_output = " ".join(error_calls)
        assert "UNKNOWN_ERROR" in error_output
        assert "Contact support for assistance" in error_output

    def test_error_id_generation(self):
        """エラーIDの生成テスト"""
        # モックロガーを設定
        mock_logger = MagicMock()
        app = MinimalCLIApp(logger=mock_logger)

        composite_error = CompositeStepFailureError(
            "テストエラー",
            error_code=ErrorCode.FILE_NOT_FOUND
        )

        app._handle_composite_step_failure(composite_error)

        # ロガーの呼び出し確認
        assert mock_logger.error.called
        error_calls = [call.args[0] for call in mock_logger.error.call_args_list]
        error_output = " ".join(error_calls)
        # エラーIDが含まれることを確認（8文字のハッシュ）
        assert "#" in error_output
        assert "FILE_NOT_FOUND#" in error_output
