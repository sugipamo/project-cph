"""
ワークフローファサードのテスト
純粋関数と既存APIの橋渡し機能をテスト
"""
import pytest
from unittest.mock import Mock, patch
from pathlib import Path
from src.pure_functions.workflow_facade import (
    PureWorkflowFacade,
    create_test_execution_data,
    create_test_step_context_data
)
from src.pure_functions.execution_context_pure import ExecutionData, StepContextData


class TestCreateTestHelpers:
    """テストヘルパー関数のテスト"""
    
    def test_create_test_execution_data_defaults(self):
        """デフォルト値でのテスト実行データ作成"""
        data = create_test_execution_data()
        
        assert isinstance(data, ExecutionData)
        assert data.command_type == "build"
        assert data.language == "python"
        assert data.contest_name == "test_contest"
        assert data.problem_name == "a"
        assert data.env_type == "local"
        assert data.workspace_path == "./workspace"
        assert data.contest_current_path == "./contest_current"
    
    def test_create_test_execution_data_custom(self):
        """カスタム値でのテスト実行データ作成"""
        data = create_test_execution_data(
            command_type="test",
            language="rust",
            contest_name="abc123",
            problem_name="b",
            env_type="docker"
        )
        
        assert data.command_type == "test"
        assert data.language == "rust"
        assert data.contest_name == "abc123"
        assert data.problem_name == "b"
        assert data.env_type == "docker"
    
    def test_create_test_execution_data_has_valid_env_json(self):
        """有効なenv_jsonを持つテスト実行データ作成"""
        data = create_test_execution_data(
            language="python",
            command_type="build"
        )
        
        assert "python" in data.env_json
        assert "commands" in data.env_json["python"]
        assert "build" in data.env_json["python"]["commands"]
        assert "steps" in data.env_json["python"]["commands"]["build"]
    
    def test_create_test_step_context_data_defaults(self):
        """デフォルト値でのテストステップコンテキストデータ作成"""
        data = create_test_step_context_data()
        
        assert isinstance(data, StepContextData)
        assert data.contest_name == "test_contest"
        assert data.problem_name == "a"
        assert data.language == "python"
        assert data.env_type == "local"
        assert data.command_type == "build"
        assert data.workspace_path == "./workspace"
        assert data.contest_current_path == "./contest_current"
    
    def test_create_test_step_context_data_custom(self):
        """カスタム値でのテストステップコンテキストデータ作成"""
        data = create_test_step_context_data(
            contest_name="xyz789",
            problem_name="c",
            language="rust",
            env_type="docker",
            command_type="test"
        )
        
        assert data.contest_name == "xyz789"
        assert data.problem_name == "c"
        assert data.language == "rust"
        assert data.env_type == "docker"
        assert data.command_type == "test"


class TestPureWorkflowFacade:
    """PureWorkflowFacadeのテスト"""
    
    def test_validate_execution_context_valid(self):
        """有効な実行コンテキストの検証"""
        # モック実行コンテキスト作成
        mock_context = Mock()
        mock_context.command_type = "build"
        mock_context.language = "python"
        mock_context.contest_name = "abc123"
        mock_context.problem_name = "a"
        mock_context.env_type = "local"
        mock_context.env_json = {
            "python": {
                "commands": {
                    "build": {"steps": []}
                }
            }
        }
        
        is_valid, errors = PureWorkflowFacade.validate_execution_context(mock_context)
        
        assert is_valid
        assert errors == []
    
    def test_validate_execution_context_invalid(self):
        """無効な実行コンテキストの検証"""
        # 無効なモック実行コンテキスト作成
        mock_context = Mock()
        mock_context.command_type = ""  # 無効
        mock_context.language = ""      # 無効
        mock_context.contest_name = "abc123"
        mock_context.problem_name = "a"
        mock_context.env_type = "invalid"  # 無効
        mock_context.env_json = {}
        
        is_valid, errors = PureWorkflowFacade.validate_execution_context(mock_context)
        
        assert not is_valid
        assert len(errors) > 0
    
    def test_validate_execution_context_none_values(self):
        """None値を含む実行コンテキストの検証"""
        mock_context = Mock()
        mock_context.command_type = None
        mock_context.language = None
        mock_context.contest_name = None
        mock_context.problem_name = None
        mock_context.env_type = None
        mock_context.env_json = None
        
        is_valid, errors = PureWorkflowFacade.validate_execution_context(mock_context)
        
        assert not is_valid
        assert len(errors) > 0
    
    @patch('src.pure_functions.workflow_facade.extract_workflow_config_pure')
    def test_plan_workflow_from_context_success(self, mock_extract):
        """成功時のワークフロー計画作成テスト"""
        from src.pure_functions.workflow_execution_pure import WorkflowConfig, WorkflowPlan
        
        # モック設定
        mock_context = Mock()
        mock_context.command_type = "build"
        mock_context.language = "python"
        mock_context.contest_name = "abc123"
        mock_context.problem_name = "a"
        mock_context.env_type = "local"
        mock_context.env_json = {"python": {"commands": {"build": {"steps": []}}}}
        mock_context.working_directory = "./work"
        mock_context.contest_current_path = "./current"
        mock_context.workspace_path = "./workspace"
        
        mock_config = WorkflowConfig(
            steps=[{"type": "shell", "cmd": ["echo", "test"]}],
            language="python",
            command_type="build",
            env_type="local"
        )
        mock_extract.return_value = mock_config
        
        # パッチした関数群
        with patch('src.pure_functions.workflow_facade.execution_data_to_step_context_pure') as mock_convert:
            with patch('src.pure_functions.workflow_facade.plan_workflow_execution_pure') as mock_plan:
                with patch('src.pure_functions.workflow_facade.validate_workflow_plan_pure') as mock_validate:
                    
                    mock_convert.return_value = Mock()
                    mock_plan.return_value = WorkflowPlan(
                        main_steps=[],
                        preparation_steps=[],
                        dependencies=[],
                        errors=[],
                        warnings=[]
                    )
                    mock_validate.return_value = []
                    
                    # 実行
                    plan = PureWorkflowFacade.plan_workflow_from_context(mock_context)
                    
                    # 検証
                    assert plan is not None
                    mock_extract.assert_called_once()
                    mock_convert.assert_called_once()
                    mock_plan.assert_called_once()
                    mock_validate.assert_called_once()
    
    @patch('src.pure_functions.workflow_facade.extract_workflow_config_pure')
    def test_plan_workflow_from_context_no_config(self, mock_extract):
        """ワークフロー設定なしの場合のテスト"""
        mock_context = Mock()
        mock_context.command_type = "build"
        mock_context.language = "python"
        mock_context.contest_name = "abc123"
        mock_context.problem_name = "a"
        mock_context.env_type = "local"
        mock_context.env_json = {}
        
        mock_extract.return_value = None
        
        plan = PureWorkflowFacade.plan_workflow_from_context(mock_context)
        
        assert plan.main_steps == []
        assert plan.preparation_steps == []
        assert plan.dependencies == []
        assert "No workflow configuration found" in plan.errors
    
    @patch('src.pure_functions.workflow_facade.extract_workflow_config_pure')
    def test_build_workflow_from_context_success(self, mock_extract):
        """成功時のワークフロー構築テスト"""
        from src.pure_functions.workflow_execution_pure import WorkflowConfig
        
        # モック設定
        mock_context = Mock()
        mock_context.command_type = "build"
        mock_context.language = "python"
        mock_context.contest_name = "abc123"
        mock_context.problem_name = "a"
        mock_context.env_type = "local"
        mock_context.env_json = {"python": {"commands": {"build": {"steps": []}}}}
        
        mock_config = WorkflowConfig(
            steps=[{"type": "shell", "cmd": ["echo", "test"]}],
            language="python",
            command_type="build",
            env_type="local"
        )
        mock_extract.return_value = mock_config
        
        with patch('src.pure_functions.workflow_facade.execution_data_to_step_context_pure') as mock_convert:
            with patch('src.pure_functions.workflow_facade.build_workflow_pure') as mock_build:
                from src.pure_functions.workflow_builder_pure import WorkflowBuildOutput
                from src.env_core.workflow.request_execution_graph import RequestExecutionGraph
                
                mock_convert.return_value = Mock()
                mock_build.return_value = WorkflowBuildOutput(
                    nodes=[],
                    edges=[],
                    errors=[],
                    warnings=[]
                )
                
                # 実行
                graph, errors, warnings = PureWorkflowFacade.build_workflow_from_context(mock_context)
                
                # 検証
                assert isinstance(graph, RequestExecutionGraph)
                assert errors == []
                assert warnings == []
                mock_extract.assert_called_once()
                mock_convert.assert_called_once()
                mock_build.assert_called_once()
    
    @patch('src.pure_functions.workflow_facade.extract_workflow_config_pure')
    def test_build_workflow_from_context_no_config(self, mock_extract):
        """ワークフロー設定なしでの構築テスト"""
        mock_context = Mock()
        mock_context.command_type = "build"
        mock_context.language = "python"
        mock_context.contest_name = "abc123"
        mock_context.problem_name = "a"
        mock_context.env_type = "local"
        mock_context.env_json = {}
        
        mock_extract.return_value = None
        
        graph, errors, warnings = PureWorkflowFacade.build_workflow_from_context(mock_context)
        
        from src.env_core.workflow.request_execution_graph import RequestExecutionGraph
        assert isinstance(graph, RequestExecutionGraph)
        assert "No workflow configuration found" in errors
        assert warnings == []
    
    def test_build_workflow_from_context_with_json_steps(self):
        """JSON stepsを直接指定した場合のテスト"""
        mock_context = Mock()
        mock_context.command_type = "build"
        mock_context.language = "python"
        mock_context.contest_name = "abc123"
        mock_context.problem_name = "a"
        mock_context.env_type = "local"
        mock_context.env_json = {}
        
        json_steps = [{"type": "shell", "cmd": ["echo", "test"]}]
        
        with patch('src.pure_functions.workflow_facade.execution_data_to_step_context_pure') as mock_convert:
            with patch('src.pure_functions.workflow_facade.build_workflow_pure') as mock_build:
                from src.pure_functions.workflow_builder_pure import WorkflowBuildOutput
                
                mock_convert.return_value = Mock()
                mock_build.return_value = WorkflowBuildOutput(
                    nodes=[],
                    edges=[],
                    errors=[],
                    warnings=[]
                )
                
                # 実行
                graph, errors, warnings = PureWorkflowFacade.build_workflow_from_context(
                    mock_context, json_steps
                )
                
                # 検証
                from src.env_core.workflow.request_execution_graph import RequestExecutionGraph
                assert isinstance(graph, RequestExecutionGraph)
                assert errors == []
                assert warnings == []


class TestDataImmutability:
    """データ不変性のテスト"""
    
    def test_execution_data_immutability(self):
        """ExecutionDataの不変性テスト"""
        data = create_test_execution_data()
        
        with pytest.raises(AttributeError):
            data.command_type = "new_command"
        
        with pytest.raises(AttributeError):
            data.language = "new_language"
    
    def test_step_context_data_immutability(self):
        """StepContextDataの不変性テスト"""
        data = create_test_step_context_data()
        
        with pytest.raises(AttributeError):
            data.contest_name = "new_contest"
        
        with pytest.raises(AttributeError):
            data.problem_name = "new_problem"


class TestIntegrationScenarios:
    """統合シナリオのテスト"""
    
    def test_complete_workflow_facade_flow(self):
        """完全なワークフローファサードのフローテスト"""
        # 1. テストデータ作成
        test_execution_data = create_test_execution_data(
            command_type="build",
            language="python",
            contest_name="abc123",
            problem_name="a"
        )
        
        # 2. モック実行コンテキスト作成
        mock_context = Mock()
        mock_context.command_type = test_execution_data.command_type
        mock_context.language = test_execution_data.language
        mock_context.contest_name = test_execution_data.contest_name
        mock_context.problem_name = test_execution_data.problem_name
        mock_context.env_type = test_execution_data.env_type
        mock_context.env_json = test_execution_data.env_json
        
        # 3. バリデーション
        is_valid, errors = PureWorkflowFacade.validate_execution_context(mock_context)
        assert is_valid
        assert errors == []
        
        # 4. ワークフロー構築（モック使用）
        with patch('src.pure_functions.workflow_facade.extract_workflow_config_pure') as mock_extract:
            mock_extract.return_value = None  # No config found
            
            graph, errors, warnings = PureWorkflowFacade.build_workflow_from_context(mock_context)
            
            from src.env_core.workflow.request_execution_graph import RequestExecutionGraph
            assert isinstance(graph, RequestExecutionGraph)
    
    def test_error_handling_consistency(self):
        """エラーハンドリングの一貫性テスト"""
        # 無効なコンテキスト
        mock_context = Mock()
        mock_context.command_type = ""
        mock_context.language = ""
        mock_context.contest_name = ""
        mock_context.problem_name = ""
        mock_context.env_type = "invalid"
        mock_context.env_json = None
        
        # バリデーションでエラーが検出される
        is_valid, validation_errors = PureWorkflowFacade.validate_execution_context(mock_context)
        assert not is_valid
        assert len(validation_errors) > 0
        
        # ワークフロー構築でも適切にエラーハンドリングされる
        with patch('src.pure_functions.workflow_facade.extract_workflow_config_pure') as mock_extract:
            mock_extract.return_value = None
            
            graph, build_errors, warnings = PureWorkflowFacade.build_workflow_from_context(mock_context)
            
            from src.env_core.workflow.request_execution_graph import RequestExecutionGraph
            assert isinstance(graph, RequestExecutionGraph)
            assert len(build_errors) > 0  # エラーが報告される


class TestPerformanceCharacteristics:
    """パフォーマンス特性のテスト"""
    
    def test_multiple_calls_consistency(self):
        """複数回呼び出しの一貫性テスト"""
        # 同じパラメータで複数回実行
        data1 = create_test_execution_data(language="python", command_type="build")
        data2 = create_test_execution_data(language="python", command_type="build")
        
        # 結果が一致することを確認
        assert data1.language == data2.language
        assert data1.command_type == data2.command_type
        assert data1.env_json == data2.env_json
    
    def test_memory_efficiency(self):
        """メモリ効率のテスト"""
        # 大量のテストデータ作成
        test_data_list = []
        for i in range(100):
            data = create_test_execution_data(
                contest_name=f"contest_{i}",
                problem_name=f"problem_{i}"
            )
            test_data_list.append(data)
        
        # データが正しく作成されることを確認
        assert len(test_data_list) == 100
        assert test_data_list[0].contest_name == "contest_0"
        assert test_data_list[99].contest_name == "contest_99"