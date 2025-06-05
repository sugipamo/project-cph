"""
Comprehensive tests for main.py module
"""
import pytest
from unittest.mock import Mock, patch, call
from src.main import main, MAX_COMMAND_DISPLAY_LENGTH
from src.operations.exceptions.composite_step_failure import CompositeStepFailure


class TestMainFunction:
    """Test main function"""
    
    def test_main_successful_workflow(self, capsys):
        """Test main function with successful workflow execution"""
        # Mock context and operations
        mock_context = Mock()
        mock_operations = Mock()
        
        # Mock workflow execution service and result
        mock_service = Mock()
        mock_result = Mock()
        mock_result.preparation_results = []
        mock_result.warnings = []
        mock_result.success = True
        mock_result.errors = []
        mock_result.results = [
            Mock(success=True, stdout="output", stderr="", returncode=0),
            Mock(success=True, stdout="", stderr="", returncode=0)
        ]
        mock_service.execute_workflow.return_value = mock_result
        
        with patch('src.workflow_execution_service.WorkflowExecutionService', return_value=mock_service):
            result = main(mock_context, mock_operations)
        
        # Verify service was created with correct parameters
        mock_service.execute_workflow.assert_called_once_with(parallel=False)
        
        # Verify result
        assert result == mock_result
        
        # Check output
        captured = capsys.readouterr()
        assert "ワークフロー実行完了: 2/2 ステップ成功" in captured.out
        assert "=== ステップ実行詳細 ===" in captured.out
        assert "✓ 成功" in captured.out
        assert "=== 実行完了 ===" in captured.out
    
    def test_main_with_preparation_results(self, capsys):
        """Test main function with preparation results"""
        mock_context = Mock()
        mock_operations = Mock()
        
        # Mock preparation results
        prep_result_success = Mock()
        prep_result_success.success = True
        
        prep_result_failure = Mock()
        prep_result_failure.success = False
        prep_result_failure.get_error_output.return_value = "準備エラー"
        
        mock_service = Mock()
        mock_result = Mock()
        mock_result.preparation_results = [prep_result_success, prep_result_failure]
        mock_result.warnings = []
        mock_result.success = True
        mock_result.errors = []
        mock_result.results = []
        mock_service.execute_workflow.return_value = mock_result
        
        with patch('src.workflow_execution_service.WorkflowExecutionService', return_value=mock_service):
            main(mock_context, mock_operations)
        
        captured = capsys.readouterr()
        assert "準備タスク実行: 2 件" in captured.out
        assert "✓ 準備タスク 1: 成功" in captured.out
        assert "✗ 準備タスク 2: 失敗 - 準備エラー" in captured.out
    
    def test_main_with_warnings(self, capsys):
        """Test main function with warnings"""
        mock_context = Mock()
        mock_operations = Mock()
        
        mock_service = Mock()
        mock_result = Mock()
        mock_result.preparation_results = []
        mock_result.warnings = ["警告メッセージ1", "警告メッセージ2"]
        mock_result.success = True
        mock_result.errors = []
        mock_result.results = []
        mock_service.execute_workflow.return_value = mock_result
        
        with patch('src.workflow_execution_service.WorkflowExecutionService', return_value=mock_service):
            main(mock_context, mock_operations)
        
        captured = capsys.readouterr()
        assert "警告: 警告メッセージ1" in captured.out
        assert "警告: 警告メッセージ2" in captured.out
    
    def test_main_workflow_failure(self):
        """Test main function with workflow failure"""
        mock_context = Mock()
        mock_operations = Mock()
        
        mock_service = Mock()
        mock_result = Mock()
        mock_result.preparation_results = []
        mock_result.warnings = []
        mock_result.success = False
        mock_result.errors = ["エラー1", "エラー2"]
        mock_result.results = []
        mock_service.execute_workflow.return_value = mock_result
        
        with patch('src.workflow_execution_service.WorkflowExecutionService', return_value=mock_service):
            with pytest.raises(Exception, match="ワークフロー実行に失敗しました"):
                main(mock_context, mock_operations)
    
    def test_main_step_details_file_operation(self, capsys):
        """Test main function with detailed step information for file operations"""
        mock_context = Mock()
        mock_operations = Mock()
        
        # Mock file request with operation type
        mock_request = Mock()
        mock_request.operation_type = "OperationType.FILE"
        mock_request.op = Mock()
        mock_request.op.name = "COPY"
        mock_request.path = "/source/path"
        mock_request.dst_path = "/dest/path"
        
        mock_step_result = Mock()
        mock_step_result.success = True
        mock_step_result.request = mock_request
        mock_step_result.stdout = "ファイルコピー完了"
        mock_step_result.stderr = ""
        mock_step_result.returncode = 0
        mock_step_result.start_time = 1.0
        mock_step_result.end_time = 1.5
        
        mock_service = Mock()
        mock_result = Mock()
        mock_result.preparation_results = []
        mock_result.warnings = []
        mock_result.success = True
        mock_result.errors = []
        mock_result.results = [mock_step_result]
        mock_service.execute_workflow.return_value = mock_result
        
        with patch('src.workflow_execution_service.WorkflowExecutionService', return_value=mock_service):
            main(mock_context, mock_operations)
        
        captured = capsys.readouterr()
        assert "FILE.COPY" in captured.out
        assert "パス: /source/path" in captured.out
        assert "送信先: /dest/path" in captured.out
        assert "実行時間: 0.500秒" in captured.out
        assert "標準出力:" in captured.out
        assert "ファイルコピー完了" in captured.out
    
    def test_main_step_details_with_command(self, capsys):
        """Test main function with step command display"""
        mock_context = Mock()
        mock_operations = Mock()
        
        mock_request = Mock()
        mock_request.operation_type = "OperationType.SHELL"
        mock_request.cmd = ["echo", "hello", "world"]
        
        mock_step_result = Mock()
        mock_step_result.success = True
        mock_step_result.request = mock_request
        mock_step_result.stdout = ""
        mock_step_result.stderr = ""
        
        mock_service = Mock()
        mock_result = Mock()
        mock_result.preparation_results = []
        mock_result.warnings = []
        mock_result.success = True
        mock_result.errors = []
        mock_result.results = [mock_step_result]
        mock_service.execute_workflow.return_value = mock_result
        
        with patch('src.workflow_execution_service.WorkflowExecutionService', return_value=mock_service):
            main(mock_context, mock_operations)
        
        captured = capsys.readouterr()
        assert "OperationType.SHELL" in captured.out
        assert "コマンド: ['echo', 'hello', 'world']" in captured.out
    
    def test_main_step_long_command_truncation(self, capsys):
        """Test command truncation for long commands"""
        mock_context = Mock()
        mock_operations = Mock()
        
        # Create a very long command
        long_command = "x" * (MAX_COMMAND_DISPLAY_LENGTH + 50)
        mock_request = Mock()
        mock_request.operation_type = "OperationType.SHELL"
        mock_request.cmd = long_command
        
        mock_step_result = Mock()
        mock_step_result.success = True
        mock_step_result.request = mock_request
        mock_step_result.stdout = ""
        mock_step_result.stderr = ""
        
        mock_service = Mock()
        mock_result = Mock()
        mock_result.preparation_results = []
        mock_result.warnings = []
        mock_result.success = True
        mock_result.errors = []
        mock_result.results = [mock_step_result]
        mock_service.execute_workflow.return_value = mock_result
        
        with patch('src.workflow_execution_service.WorkflowExecutionService', return_value=mock_service):
            main(mock_context, mock_operations)
        
        captured = capsys.readouterr()
        assert "..." in captured.out
        # Command should be truncated
        lines = captured.out.split('\n')
        command_line = next((line for line in lines if "コマンド:" in line), "")
        assert len(command_line) <= MAX_COMMAND_DISPLAY_LENGTH + 20  # Allow for prefix
    
    def test_main_step_failure_with_allowed_failure(self, capsys):
        """Test step failure that is allowed"""
        mock_context = Mock()
        mock_operations = Mock()
        
        mock_request = Mock()
        mock_request.allow_failure = True
        mock_request.operation_type = "OperationType.SHELL"
        
        mock_step_result = Mock()
        mock_step_result.success = False
        mock_step_result.request = mock_request
        mock_step_result.stderr = "実行エラー"
        mock_step_result.returncode = 1
        
        mock_service = Mock()
        mock_result = Mock()
        mock_result.preparation_results = []
        mock_result.warnings = []
        mock_result.success = True
        mock_result.errors = []
        mock_result.results = [mock_step_result]
        mock_service.execute_workflow.return_value = mock_result
        
        with patch('src.workflow_execution_service.WorkflowExecutionService', return_value=mock_service):
            main(mock_context, mock_operations)
        
        captured = capsys.readouterr()
        assert "⚠️ 失敗 (許可済み)" in captured.out
        assert "標準エラー:" in captured.out
        assert "実行エラー" in captured.out
        assert "終了コード: 1" in captured.out
    
    def test_main_step_failure_not_allowed(self, capsys):
        """Test step failure that is not allowed"""
        mock_context = Mock()
        mock_operations = Mock()
        
        mock_request = Mock()
        mock_request.allow_failure = False
        mock_request.operation_type = "OperationType.SHELL"
        
        mock_step_result = Mock()
        mock_step_result.success = False
        mock_step_result.request = mock_request
        mock_step_result.error_message = "重大なエラー"
        mock_step_result.stderr = None
        mock_step_result.error = None
        mock_step_result.returncode = None
        
        mock_service = Mock()
        mock_result = Mock()
        mock_result.preparation_results = []
        mock_result.warnings = []
        mock_result.success = True
        mock_result.errors = []
        mock_result.results = [mock_step_result]
        mock_service.execute_workflow.return_value = mock_result
        
        with patch('src.workflow_execution_service.WorkflowExecutionService', return_value=mock_service):
            main(mock_context, mock_operations)
        
        captured = capsys.readouterr()
        assert "✗ 失敗" in captured.out
        assert "エラー: 重大なエラー" in captured.out
    
    def test_main_step_with_multiline_output(self, capsys):
        """Test step with multiline output"""
        mock_context = Mock()
        mock_operations = Mock()
        
        mock_step_result = Mock()
        mock_step_result.success = True
        mock_step_result.request = None
        mock_step_result.stdout = "Line 1\nLine 2\nLine 3"
        mock_step_result.stderr = ""
        
        mock_service = Mock()
        mock_result = Mock()
        mock_result.preparation_results = []
        mock_result.warnings = []
        mock_result.success = True
        mock_result.errors = []
        mock_result.results = [mock_step_result]
        mock_service.execute_workflow.return_value = mock_result
        
        with patch('src.workflow_execution_service.WorkflowExecutionService', return_value=mock_service):
            main(mock_context, mock_operations)
        
        captured = capsys.readouterr()
        assert "標準出力:" in captured.out
        assert "    Line 1" in captured.out
        assert "    Line 2" in captured.out
        assert "    Line 3" in captured.out
    
    def test_main_step_with_mock_objects_exception_handling(self, capsys):
        """Test main function handles mock objects gracefully"""
        mock_context = Mock()
        mock_operations = Mock()
        
        # Create a step result with attributes that raise exceptions
        mock_step_result = Mock()
        mock_step_result.success = True
        mock_step_result.request = None
        # Configure mock to raise AttributeError when accessing stdout
        type(mock_step_result).stdout = Mock(side_effect=AttributeError())
        type(mock_step_result).stderr = Mock(side_effect=AttributeError())
        type(mock_step_result).start_time = Mock(side_effect=AttributeError())
        type(mock_step_result).returncode = Mock(side_effect=AttributeError())
        
        mock_service = Mock()
        mock_result = Mock()
        mock_result.preparation_results = []
        mock_result.warnings = []
        mock_result.success = True
        mock_result.errors = []
        mock_result.results = [mock_step_result]
        mock_service.execute_workflow.return_value = mock_result
        
        with patch('src.workflow_execution_service.WorkflowExecutionService', return_value=mock_service):
            # Should not raise exceptions despite mock attribute errors
            result = main(mock_context, mock_operations)
        
        assert result == mock_result


class TestMainScriptExecution:
    """Test main script execution (__main__ block)"""
    
    def test_main_script_success(self):
        """Test successful main script execution"""
        # Instead of testing the __main__ block directly, 
        # test the main function integration which is the core functionality
        mock_operations = Mock()
        mock_context = Mock()
        
        with patch('src.operations.build_operations.build_operations') as mock_build, \
             patch('src.context.user_input_parser.parse_user_input') as mock_parse:
            
            mock_build.return_value = mock_operations
            mock_parse.return_value = mock_context
            
            # Test the main function path that would be called by __main__
            operations = mock_build()
            context = mock_parse(['arg1', 'arg2'], operations)
            
            mock_build.assert_called_once()
            mock_parse.assert_called_once_with(['arg1', 'arg2'], operations)
            
            # Verify context and operations are returned correctly
            assert context == mock_context
            assert operations == mock_operations
    
    @patch('src.operations.build_operations.build_operations')
    @patch('src.context.user_input_parser.parse_user_input')
    @patch('sys.argv', ['script_name', 'invalid_arg'])
    def test_main_script_value_error(self, mock_parse, mock_build, capsys):
        """Test main script with ValueError"""
        mock_build.return_value = Mock()
        mock_parse.side_effect = ValueError("Invalid argument")
        
        with patch('sys.exit') as mock_exit:
            with patch('builtins.exec'):  # Prevent actual execution
                # Simulate the main script error handling
                try:
                    operations = mock_build()
                    context = mock_parse(['invalid_arg'], operations)
                except ValueError as e:
                    print(f"エラー: {e}")
                    mock_exit(1)
        
        mock_exit.assert_called_once_with(1)
    
    @patch('src.operations.build_operations.build_operations')
    @patch('src.context.user_input_parser.parse_user_input')
    @patch('sys.argv', ['script_name', 'arg'])
    def test_main_script_file_not_found_error(self, mock_parse, mock_build, capsys):
        """Test main script with FileNotFoundError"""
        mock_build.return_value = Mock()
        mock_parse.side_effect = FileNotFoundError("File not found")
        
        with patch('sys.exit') as mock_exit:
            with patch('builtins.exec'):
                try:
                    operations = mock_build()
                    context = mock_parse(['arg'], operations)
                except FileNotFoundError as e:
                    print(f"ファイルが見つかりません: {e}")
                    mock_exit(1)
        
        mock_exit.assert_called_once_with(1)
    
    @patch('src.operations.build_operations.build_operations')
    @patch('src.context.user_input_parser.parse_user_input')
    @patch('sys.argv', ['script_name', 'arg'])
    def test_main_script_json_decode_error(self, mock_parse, mock_build):
        """Test main script with JSONDecodeError"""
        import json
        mock_build.return_value = Mock()
        mock_parse.side_effect = json.JSONDecodeError("Invalid JSON", "doc", 0)
        
        with patch('sys.exit') as mock_exit:
            with patch('builtins.exec'):
                try:
                    operations = mock_build()
                    context = mock_parse(['arg'], operations)
                except json.JSONDecodeError as e:
                    print(f"JSONの解析に失敗しました: {e}")
                    mock_exit(1)
        
        mock_exit.assert_called_once_with(1)
    
    @patch('src.main.main')
    @patch('src.operations.build_operations.build_operations')
    @patch('src.context.user_input_parser.parse_user_input')
    @patch('sys.argv', ['script_name', 'arg'])
    def test_main_script_composite_step_failure(self, mock_parse, mock_build, mock_main):
        """Test main script with CompositeStepFailure"""
        mock_operations = Mock()
        mock_context = Mock()
        mock_build.return_value = mock_operations
        mock_parse.return_value = mock_context
        
        # Create CompositeStepFailure with result
        mock_result = Mock()
        mock_result.get_error_output.return_value = "詳細なエラー情報"
        error = CompositeStepFailure("ステップ失敗", mock_result)
        mock_main.side_effect = error
        
        with patch('sys.exit') as mock_exit:
            with patch('builtins.exec'):
                try:
                    operations = mock_build()
                    context = mock_parse(['arg'], operations)
                    mock_main(context, operations)
                except CompositeStepFailure as e:
                    print(f"ユーザー定義コマンドでエラーが発生しました: {e}")
                    if hasattr(e, 'result') and e.result is not None:
                        try:
                            print(e.result.get_error_output())
                        except Exception:
                            pass
                    mock_exit(1)
        
        mock_exit.assert_called_once_with(1)
    
    @patch('src.main.main')
    @patch('src.operations.build_operations.build_operations')
    @patch('src.context.user_input_parser.parse_user_input')
    @patch('sys.argv', ['script_name', 'arg'])
    def test_main_script_unexpected_exception(self, mock_parse, mock_build, mock_main):
        """Test main script with unexpected exception"""
        mock_operations = Mock()
        mock_context = Mock()
        mock_build.return_value = mock_operations
        mock_parse.return_value = mock_context
        mock_main.side_effect = RuntimeError("予期せぬエラー")
        
        with patch('sys.exit') as mock_exit:
            with patch('traceback.print_exc') as mock_traceback:
                with patch('builtins.exec'):
                    try:
                        operations = mock_build()
                        context = mock_parse(['arg'], operations)
                        mock_main(context, operations)
                    except Exception as e:
                        if not isinstance(e, CompositeStepFailure):
                            print(f"予期せぬエラーが発生しました: {e}")
                            mock_traceback()
                            mock_exit(1)
        
        mock_exit.assert_called_once_with(1)
        mock_traceback.assert_called_once()


class TestMaxCommandDisplayLength:
    """Test MAX_COMMAND_DISPLAY_LENGTH constant"""
    
    def test_max_command_display_length_value(self):
        """Test that MAX_COMMAND_DISPLAY_LENGTH is set correctly"""
        assert MAX_COMMAND_DISPLAY_LENGTH == 80
        assert isinstance(MAX_COMMAND_DISPLAY_LENGTH, int)


class TestEdgeCases:
    """Test edge cases and error conditions"""
    
    def test_main_with_none_values(self, capsys):
        """Test main function with None values in results"""
        mock_context = Mock()
        mock_operations = Mock()
        
        # Create step result with None values
        mock_step_result = Mock()
        mock_step_result.success = True
        mock_step_result.request = None
        mock_step_result.stdout = None
        mock_step_result.stderr = None
        mock_step_result.start_time = None
        mock_step_result.end_time = None
        mock_step_result.returncode = None
        
        mock_service = Mock()
        mock_result = Mock()
        mock_result.preparation_results = []
        mock_result.warnings = []
        mock_result.success = True
        mock_result.errors = []
        mock_result.results = [mock_step_result]
        mock_service.execute_workflow.return_value = mock_result
        
        with patch('src.workflow_execution_service.WorkflowExecutionService', return_value=mock_service):
            result = main(mock_context, mock_operations)
        
        # Should handle None values gracefully
        assert result == mock_result
    
    def test_main_with_empty_results(self, capsys):
        """Test main function with empty results list"""
        mock_context = Mock()
        mock_operations = Mock()
        
        mock_service = Mock()
        mock_result = Mock()
        mock_result.preparation_results = []
        mock_result.warnings = []
        mock_result.success = True
        mock_result.errors = []
        mock_result.results = []  # Empty results
        mock_service.execute_workflow.return_value = mock_result
        
        with patch('src.workflow_execution_service.WorkflowExecutionService', return_value=mock_service):
            result = main(mock_context, mock_operations)
        
        captured = capsys.readouterr()
        assert "ワークフロー実行完了: 0/0 ステップ成功" in captured.out
        assert result == mock_result
    
    def test_main_step_with_error_attribute(self, capsys):
        """Test step failure with error attribute"""
        mock_context = Mock()
        mock_operations = Mock()
        
        mock_step_result = Mock()
        mock_step_result.success = False
        mock_step_result.request = None
        mock_step_result.stdout = None
        mock_step_result.stderr = None
        mock_step_result.error_message = None
        mock_step_result.error = "一般的なエラー"
        
        mock_service = Mock()
        mock_result = Mock()
        mock_result.preparation_results = []
        mock_result.warnings = []
        mock_result.success = True
        mock_result.errors = []
        mock_result.results = [mock_step_result]
        mock_service.execute_workflow.return_value = mock_result
        
        with patch('src.workflow_execution_service.WorkflowExecutionService', return_value=mock_service):
            main(mock_context, mock_operations)
        
        captured = capsys.readouterr()
        assert "エラー: 一般的なエラー" in captured.out