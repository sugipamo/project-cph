"""
GraphBasedWorkflowBuilderのテスト（新API用）
"""
import pytest
from unittest.mock import Mock, MagicMock, patch
from src.env_core.workflow.graph_based_workflow_builder import GraphBasedWorkflowBuilder
from src.env_core.workflow.request_execution_graph import RequestExecutionGraph
from src.context.resolver.config_node import ConfigNode
from src.env_core.step.step import Step, StepType


class TestGraphBasedWorkflowBuilder:
    """GraphBasedWorkflowBuilderのテストクラス（新API用）"""
    
    @pytest.fixture
    def mock_context(self):
        """モックコンテキストを生成"""
        context = Mock()
        context.contest_name = "test_contest"
        context.problem_name = "test_problem"
        context.language = "python"
        context.env_type = "local"
        context.command_type = "run"
        context.env_json = None  # No debug config
        return context
    
    @pytest.fixture
    def builder(self, mock_context):
        """GraphBasedWorkflowBuilderのインスタンスを生成（新API使用）"""
        return GraphBasedWorkflowBuilder.from_context(mock_context)
    
    @pytest.fixture
    def sample_json_steps(self):
        """サンプルのJSONステップデータ"""
        return [
            {
                "type": "mkdir",
                "cmd": ["/tmp/test"]
            },
            {
                "type": "touch",
                "cmd": ["/tmp/test/file.txt"]
            },
            {
                "type": "copy",
                "cmd": ["/tmp/test/file.txt", "/tmp/test/copy.txt"]
            }
        ]
    
    def test_from_context(self, mock_context):
        """from_contextメソッドのテスト（新API）"""
        builder = GraphBasedWorkflowBuilder.from_context(mock_context)
        
        assert isinstance(builder, GraphBasedWorkflowBuilder)
        assert builder.context == mock_context
    
    def test_from_controller(self):
        """from_controllerメソッドのテスト（既存互換性）"""
        mock_controller = Mock()
        mock_controller.env_context = Mock()
        mock_operations = Mock()
        
        with patch('src.env_core.step.workflow.create_step_context_from_env_context') as mock_create:
            mock_context = Mock()
            mock_create.return_value = mock_context
            
            builder = GraphBasedWorkflowBuilder.from_controller(
                mock_controller, 
                mock_operations
            )
            
            assert isinstance(builder, GraphBasedWorkflowBuilder)
            assert builder.context == mock_context
            mock_create.assert_called_once_with(mock_controller.env_context)
    
    @patch('src.env_core.workflow.graph_based_workflow_builder.generate_steps_from_json')
    @patch('src.env_core.workflow.graph_based_workflow_builder.resolve_dependencies')
    @patch('src.env_core.workflow.graph_based_workflow_builder.optimize_workflow_steps')
    def test_build_graph_from_json_steps_success(
        self, 
        mock_optimize, 
        mock_resolve, 
        mock_generate,
        builder, 
        sample_json_steps
    ):
        """JSONステップからグラフ構築のテスト（成功）"""
        # モックの設定
        mock_steps = [
            Step(StepType.MKDIR, ["/tmp/test"]),
            Step(StepType.TOUCH, ["/tmp/test/file.txt"])
        ]
        
        mock_generation_result = Mock()
        mock_generation_result.is_success = True
        mock_generation_result.steps = mock_steps
        mock_generation_result.errors = []
        mock_generation_result.warnings = ["warning1"]
        
        mock_generate.return_value = mock_generation_result
        mock_resolve.return_value = mock_steps
        mock_optimize.return_value = mock_steps
        
        # 実行
        graph, errors, warnings = builder.build_graph_from_json_steps(sample_json_steps)
        
        # 検証
        assert isinstance(graph, RequestExecutionGraph)
        assert len(errors) == 0
        assert warnings == ["warning1"]
        
        # 関数が呼ばれたか確認
        mock_generate.assert_called_once()
        mock_resolve.assert_called_once_with(mock_steps, mock_generate.call_args[0][1])
        mock_optimize.assert_called_once_with(mock_steps)
    
    @patch('src.env_core.workflow.graph_based_workflow_builder.generate_steps_from_json')
    def test_build_graph_from_json_steps_error(
        self, 
        mock_generate,
        builder, 
        sample_json_steps
    ):
        """JSONステップからグラフ構築のテスト（エラー）"""
        # エラーを含む結果を返す
        mock_generation_result = Mock()
        mock_generation_result.is_success = False
        mock_generation_result.steps = []
        mock_generation_result.errors = ["error1", "error2"]
        mock_generation_result.warnings = []
        
        mock_generate.return_value = mock_generation_result
        
        # 実行
        graph, errors, warnings = builder.build_graph_from_json_steps(sample_json_steps)
        
        # 検証
        assert isinstance(graph, RequestExecutionGraph)
        assert len(graph.nodes) == 0  # 空のグラフ
        assert errors == ["error1", "error2"]
        assert warnings == []
    
    def test_build_graph_from_nodes(self, builder):
        """ConfigNodeからグラフ構築のテスト"""
        # ConfigNodeを作成
        node1 = ConfigNode("step1")
        node1.value = {"type": "mkdir", "cmd": ["/tmp/test"]}
        
        node2 = ConfigNode("step2")
        node2.value = {"type": "touch", "cmd": ["/tmp/test/file.txt"]}
        
        node3 = ConfigNode("step3")
        node3.value = None  # 無効なノード
        
        with patch.object(builder, 'build_graph_from_json_steps') as mock_build:
            mock_build.return_value = (RequestExecutionGraph(), [], [])
            
            # 実行
            graph, errors, warnings = builder.build_graph_from_nodes([node1, node2, node3])
            
            # 検証
            mock_build.assert_called_once()
            call_args = mock_build.call_args[0][0]
            assert len(call_args) == 2  # node3は除外される
            assert call_args[0] == {"type": "mkdir", "cmd": ["/tmp/test"]}
            assert call_args[1] == {"type": "touch", "cmd": ["/tmp/test/file.txt"]}
    
    def test_build_composite_from_graph(self, builder):
        """グラフからCompositeRequest構築のテスト"""
        # モックグラフを作成
        mock_graph = Mock(spec=RequestExecutionGraph)
        
        with patch('src.env_core.workflow.graph_based_workflow_builder.GraphToCompositeAdapter') as MockAdapter:
            mock_composite = Mock()
            MockAdapter.to_composite_request.return_value = mock_composite
            
            # 実行
            result = builder.build_composite_from_graph(mock_graph)
            
            # 検証
            assert result == mock_composite
            MockAdapter.to_composite_request.assert_called_once_with(mock_graph)
    
    def test_validate_graph(self, builder):
        """グラフ検証のテスト"""
        # 正常なグラフ
        graph = RequestExecutionGraph()
        node1 = Mock()
        node1.id = "node1"
        node1.request = Mock()
        graph.add_request_node(node1)
        
        is_valid, messages = builder.validate_graph(graph)
        assert is_valid
        assert any("1 execution groups" in msg for msg in messages)
        
        # 空のグラフ
        empty_graph = RequestExecutionGraph()
        is_valid, messages = builder.validate_graph(empty_graph)
        assert not is_valid
        assert any("No executable nodes" in msg for msg in messages)