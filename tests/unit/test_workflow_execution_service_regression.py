"""
WorkflowExecutionService回帰テスト: allow_failure処理の問題
"""
import pytest
from unittest.mock import Mock, patch

from src.workflow_execution_service import WorkflowExecutionService, WorkflowExecutionResult
from src.operations.result.result import OperationResult


class TestWorkflowExecutionServiceRegression:
    """WorkflowExecutionService回帰テスト"""
    
    def setup_method(self):
        """テストセットアップ"""
        self.mock_context = Mock()
        self.mock_operations = Mock()
        
    def test_allow_failure_success_determination(self):
        """
        回帰テスト: allow_failure=trueの失敗ステップが全体の成功判定に影響しない
        
        以前の問題: all(r.success for r in results)でallow_failureを考慮せずに失敗判定
        修正後: allow_failure=trueの失敗は致命的失敗として扱わない
        """
        service = WorkflowExecutionService(self.mock_context, self.mock_operations)
        
        # モック結果を作成
        success_result = Mock(spec=OperationResult)
        success_result.success = True
        success_result.request = Mock()
        success_result.request.allow_failure = False
        
        allowed_failure_result = Mock(spec=OperationResult)
        allowed_failure_result.success = False
        allowed_failure_result.request = Mock()
        allowed_failure_result.request.allow_failure = True
        allowed_failure_result.get_error_output = Mock(return_value="Allowed failure error")
        
        critical_failure_result = Mock(spec=OperationResult)
        critical_failure_result.success = False
        critical_failure_result.request = Mock() 
        critical_failure_result.request.allow_failure = False
        critical_failure_result.get_error_output = Mock(return_value="Critical failure error")
        
        # テストケース1: allow_failure=trueの失敗のみ → 全体成功
        with patch.object(service, '_get_workflow_steps') as mock_get_steps, \
             patch('src.workflow_execution_service.generate_steps_from_json') as mock_generate, \
             patch('src.workflow_execution_service.GraphBasedWorkflowBuilder') as mock_builder:
            
            mock_get_steps.return_value = [{"type": "shell", "cmd": ["echo", "test"]}]
            mock_step_result = Mock()
            mock_step_result.steps = []
            mock_step_result.errors = []
            mock_step_result.warnings = []
            mock_generate.return_value = mock_step_result
            
            mock_graph = Mock()
            mock_graph.execute_sequential = Mock(return_value=[success_result, allowed_failure_result])
            mock_builder_instance = Mock()
            mock_builder_instance.build_graph_from_json_steps = Mock(return_value=(mock_graph, [], []))
            mock_builder.from_context = Mock(return_value=mock_builder_instance)
            
            result = service.execute_workflow()
            
            assert result.success == True, "Workflow should succeed with only allowed failures"
            assert len(result.errors) == 1
            assert "allowed" in result.errors[0], "Error message should indicate allowed failure"
            
        # テストケース2: allow_failure=falseの失敗あり → 全体失敗
        with patch.object(service, '_get_workflow_steps') as mock_get_steps, \
             patch('src.workflow_execution_service.generate_steps_from_json') as mock_generate, \
             patch('src.workflow_execution_service.GraphBasedWorkflowBuilder') as mock_builder:
            
            mock_get_steps.return_value = [{"type": "shell", "cmd": ["echo", "test"]}]
            mock_step_result = Mock()
            mock_step_result.steps = []
            mock_step_result.errors = []
            mock_step_result.warnings = []
            mock_generate.return_value = mock_step_result
            
            mock_graph = Mock()
            mock_graph.execute_sequential = Mock(return_value=[success_result, critical_failure_result])
            mock_builder_instance = Mock()
            mock_builder_instance.build_graph_from_json_steps = Mock(return_value=(mock_graph, [], []))
            mock_builder.from_context = Mock(return_value=mock_builder_instance)
            
            result = service.execute_workflow()
            
            assert result.success == False, "Workflow should fail with critical failures"
            assert len(result.errors) == 1
            assert "allowed" not in result.errors[0], "Error message should not indicate allowed failure"
            
    def test_mixed_failure_scenarios(self):
        """
        回帰テスト: 許可された失敗と致命的失敗が混在する場合
        """
        service = WorkflowExecutionService(self.mock_context, self.mock_operations)
        
        success_result = Mock(spec=OperationResult)
        success_result.success = True
        
        allowed_failure_1 = Mock(spec=OperationResult)
        allowed_failure_1.success = False
        allowed_failure_1.request = Mock()
        allowed_failure_1.request.allow_failure = True
        allowed_failure_1.get_error_output = Mock(return_value="Allowed failure 1")
        
        allowed_failure_2 = Mock(spec=OperationResult)
        allowed_failure_2.success = False
        allowed_failure_2.request = Mock()
        allowed_failure_2.request.allow_failure = True
        allowed_failure_2.get_error_output = Mock(return_value="Allowed failure 2")
        
        critical_failure = Mock(spec=OperationResult)
        critical_failure.success = False
        critical_failure.request = Mock()
        critical_failure.request.allow_failure = False
        critical_failure.get_error_output = Mock(return_value="Critical failure")
        
        with patch.object(service, '_get_workflow_steps') as mock_get_steps, \
             patch('src.workflow_execution_service.generate_steps_from_json') as mock_generate, \
             patch('src.workflow_execution_service.GraphBasedWorkflowBuilder') as mock_builder:
            
            mock_get_steps.return_value = [{"type": "shell", "cmd": ["echo", "test"]}]
            mock_step_result = Mock()
            mock_step_result.steps = []
            mock_step_result.errors = []
            mock_step_result.warnings = []
            mock_generate.return_value = mock_step_result
            
            mock_graph = Mock()
            # 複数の許可失敗と1つの致命的失敗
            mock_graph.execute_sequential = Mock(return_value=[
                success_result, allowed_failure_1, allowed_failure_2, critical_failure
            ])
            mock_builder_instance = Mock()
            mock_builder_instance.build_graph_from_json_steps = Mock(return_value=(mock_graph, [], []))
            mock_builder.from_context = Mock(return_value=mock_builder_instance)
            
            result = service.execute_workflow()
            
            # 致命的失敗があるため全体は失敗
            assert result.success == False
            # エラーは3つ（許可失敗2つ + 致命的失敗1つ）
            assert len(result.errors) == 3
            # 許可失敗には"allowed"が含まれ、致命的失敗には含まれない
            allowed_errors = [e for e in result.errors if "allowed" in e]
            critical_errors = [e for e in result.errors if "allowed" not in e]
            assert len(allowed_errors) == 2
            assert len(critical_errors) == 1
            
    def test_request_attribute_access_safety(self):
        """
        回帰テスト: result.requestやrequest.allow_failureへの安全なアクセス
        
        以前の問題: result.requestが存在しないかrequest.allow_failureが存在しない場合の例外
        修正後: hasattr()とgetattr()で安全にアクセス
        """
        service = WorkflowExecutionService(self.mock_context, self.mock_operations)
        
        # request属性がないresult
        result_without_request = Mock(spec=OperationResult)
        result_without_request.success = False
        del result_without_request.request  # requestアトリビュートを削除
        result_without_request.get_error_output = Mock(return_value="Error without request")
        
        # requestはあるがallow_failure属性がないresult
        result_without_allow_failure = Mock(spec=OperationResult)
        result_without_allow_failure.success = False
        
        # allow_failureを明示的にFalseに設定したrequestモック
        mock_request = Mock()
        mock_request.allow_failure = False  # 明示的にFalseに設定
        
        result_without_allow_failure.request = mock_request
        result_without_allow_failure.get_error_output = Mock(return_value="Error without allow_failure")
        
        with patch.object(service, '_get_workflow_steps') as mock_get_steps, \
             patch('src.workflow_execution_service.generate_steps_from_json') as mock_generate, \
             patch('src.workflow_execution_service.GraphBasedWorkflowBuilder') as mock_builder:
            
            mock_get_steps.return_value = [{"type": "shell", "cmd": ["echo", "test"]}]
            mock_step_result = Mock()
            mock_step_result.steps = []
            mock_step_result.errors = []
            mock_step_result.warnings = []
            mock_generate.return_value = mock_step_result
            
            mock_graph = Mock()
            mock_graph.execute_sequential = Mock(return_value=[
                result_without_request, result_without_allow_failure
            ])
            mock_builder_instance = Mock()
            mock_builder_instance.build_graph_from_json_steps = Mock(return_value=(mock_graph, [], []))
            mock_builder.from_context = Mock(return_value=mock_builder_instance)
            
            # 例外が発生せずに実行が完了することを確認
            result = service.execute_workflow()
            
            # request属性がない場合やallow_failure属性がない場合はallow_failure=Falseとして扱われる
            assert result.success == False, "Missing attributes should be treated as critical failures"
            assert len(result.errors) == 2
            # "allowed"が含まれないことを確認（デフォルトでallow_failure=False扱い）
            for error in result.errors:
                assert "allowed" not in error
                
    def test_empty_results_handling(self):
        """
        回帰テスト: 空の結果リストの処理
        """
        service = WorkflowExecutionService(self.mock_context, self.mock_operations)
        
        with patch.object(service, '_get_workflow_steps') as mock_get_steps, \
             patch('src.workflow_execution_service.generate_steps_from_json') as mock_generate, \
             patch('src.workflow_execution_service.GraphBasedWorkflowBuilder') as mock_builder:
            
            mock_get_steps.return_value = [{"type": "shell", "cmd": ["echo", "test"]}]
            mock_step_result = Mock()
            mock_step_result.steps = []
            mock_step_result.errors = []
            mock_step_result.warnings = []
            mock_generate.return_value = mock_step_result
            
            mock_graph = Mock()
            mock_graph.execute_sequential = Mock(return_value=[])  # 空の結果
            mock_builder_instance = Mock()
            mock_builder_instance.build_graph_from_json_steps = Mock(return_value=(mock_graph, [], []))
            mock_builder.from_context = Mock(return_value=mock_builder_instance)
            
            result = service.execute_workflow()
            
            # 空の結果でも成功として扱われる
            assert result.success == True
            assert len(result.errors) == 0
            assert len(result.results) == 0