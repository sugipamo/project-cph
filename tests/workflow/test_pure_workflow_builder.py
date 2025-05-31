"""
純粋なWorkflowBuilder のテスト（operations非依存）
"""
import pytest
from unittest.mock import Mock, patch
from src.env_core.workflow.graph_based_workflow_builder import GraphBasedWorkflowBuilder
from src.env_core.workflow.request_execution_graph import RequestExecutionGraph
from src.env_core.step.step import StepContext, Step, StepType
from src.context.resolver.config_node import ConfigNode


class TestPureWorkflowBuilder:
    """純粋なWorkflowBuilderのテストクラス"""
    
    @pytest.fixture
    def step_context(self):
        """テスト用StepContext"""
        return StepContext(
            contest_name="test_contest",
            problem_name="test_problem",
            language="python",
            env_type="local",
            command_type="run",
            workspace_path="./workspace",
            contest_current_path="./contest_current"
        )
    
    @pytest.fixture
    def builder(self, step_context):
        """純粋なGraphBasedWorkflowBuilder"""
        return GraphBasedWorkflowBuilder.from_context(step_context)
    
    def test_builder_creation_from_context(self, step_context):
        """コンテキストからのビルダー作成テスト"""
        builder = GraphBasedWorkflowBuilder.from_context(step_context)
        
        assert builder.context == step_context
        assert isinstance(builder, GraphBasedWorkflowBuilder)
    
    def test_builder_creation_default_context(self):
        """デフォルトコンテキストでのビルダー作成テスト"""
        builder = GraphBasedWorkflowBuilder()
        
        assert builder.context is None
    
    @patch('src.env_core.workflow.graph_based_workflow_builder.generate_steps_from_json')
    @patch('src.env_core.workflow.graph_based_workflow_builder.resolve_dependencies')
    @patch('src.env_core.workflow.graph_based_workflow_builder.optimize_workflow_steps')
    def test_build_graph_from_json_steps_success(
        self, 
        mock_optimize, 
        mock_resolve, 
        mock_generate,
        builder
    ):
        """JSONステップからのグラフ生成成功テスト"""
        # モック設定
        mock_steps = [
            Step(type=StepType.MKDIR, cmd=["./test"], allow_failure=False),
            Step(type=StepType.TOUCH, cmd=["./test/file.txt"], allow_failure=False)
        ]
        
        mock_generation_result = Mock()
        mock_generation_result.is_success = True
        mock_generation_result.steps = mock_steps
        mock_generation_result.errors = []
        mock_generation_result.warnings = []
        
        mock_generate.return_value = mock_generation_result
        mock_resolve.return_value = mock_steps
        mock_optimize.return_value = mock_steps
        
        json_steps = [
            {"type": "mkdir", "cmd": ["./test"]},
            {"type": "touch", "cmd": ["./test/file.txt"]}
        ]
        
        with patch.object(builder, '_build_graph_from_steps') as mock_build:
            mock_graph = RequestExecutionGraph()
            mock_build.return_value = mock_graph
            
            graph, errors, warnings = builder.build_graph_from_json_steps(json_steps)
            
            assert isinstance(graph, RequestExecutionGraph)
            assert errors == []
            assert warnings == []
            mock_generate.assert_called_once()
            mock_resolve.assert_called_once_with(mock_steps, builder.context)
            mock_optimize.assert_called_once_with(mock_steps)
            mock_build.assert_called_once_with(mock_steps)
    
    @patch('src.env_core.workflow.graph_based_workflow_builder.generate_steps_from_json')
    def test_build_graph_from_json_steps_failure(self, mock_generate, builder):
        """JSONステップからのグラフ生成失敗テスト"""
        # エラーのあるgeneration_result
        mock_generation_result = Mock()
        mock_generation_result.is_success = False
        mock_generation_result.errors = ["Invalid step type"]
        mock_generation_result.warnings = ["Deprecated syntax"]
        
        mock_generate.return_value = mock_generation_result
        
        json_steps = [{"type": "invalid", "cmd": []}]
        
        graph, errors, warnings = builder.build_graph_from_json_steps(json_steps)
        
        assert isinstance(graph, RequestExecutionGraph)
        assert len(graph.nodes) == 0  # 空のグラフ
        assert "Invalid step type" in errors
        assert "Deprecated syntax" in warnings
    
    def test_build_graph_from_json_steps_default_context(self):
        """デフォルトコンテキストでのグラフ生成テスト"""
        builder = GraphBasedWorkflowBuilder()  # contextなし
        
        json_steps = [{"type": "mkdir", "cmd": ["./test"]}]
        
        with patch('src.env_core.workflow.graph_based_workflow_builder.generate_steps_from_json') as mock_generate:
            mock_generation_result = Mock()
            mock_generation_result.is_success = True
            mock_generation_result.steps = []
            mock_generation_result.errors = []
            mock_generation_result.warnings = []
            mock_generate.return_value = mock_generation_result
            
            graph, errors, warnings = builder.build_graph_from_json_steps(json_steps)
            
            # デフォルトコンテキストが作成されて使用される
            call_args = mock_generate.call_args
            context_used = call_args[0][1]  # 2番目の引数がcontext
            
            assert context_used.contest_name == ""
            assert context_used.env_type == "local"
            assert context_used.workspace_path == "./workspace"
    
    def test_build_graph_from_nodes(self, builder):
        """ConfigNodeからのグラフ生成テスト"""
        # モックConfigNode
        node1 = Mock(spec=ConfigNode)
        node1.value = {"type": "mkdir", "cmd": ["./test"]}
        
        node2 = Mock(spec=ConfigNode)
        node2.value = {"type": "touch", "cmd": ["./test/file.txt"]}
        
        node3 = Mock(spec=ConfigNode)
        node3.value = None  # 無効なnode
        
        step_nodes = [node1, node2, node3]
        
        with patch.object(builder, 'build_graph_from_json_steps') as mock_build:
            mock_build.return_value = (RequestExecutionGraph(), [], [])
            
            graph, errors, warnings = builder.build_graph_from_nodes(step_nodes)
            
            # JSON形式に変換されて呼び出される
            call_args = mock_build.call_args[0][0]
            assert len(call_args) == 2  # 有効なnode2つのみ
            assert call_args[0] == {"type": "mkdir", "cmd": ["./test"]}
            assert call_args[1] == {"type": "touch", "cmd": ["./test/file.txt"]}
    
    def test_build_composite_from_graph(self, builder):
        """グラフからCompositeRequestの生成テスト"""
        graph = RequestExecutionGraph()
        
        with patch('src.env_core.workflow.graph_to_composite_adapter.GraphToCompositeAdapter.to_composite_request') as mock_convert:
            mock_composite = Mock()
            mock_convert.return_value = mock_composite
            
            result = builder.build_composite_from_graph(graph)
            
            assert result == mock_composite
            mock_convert.assert_called_once_with(graph)
    
    @patch('src.env_core.workflow.pure_request_factory.PureRequestFactory.create_request_from_step')
    def test_step_to_request_success(self, mock_factory, builder):
        """StepからRequest生成成功テスト"""
        step = Step(type=StepType.MKDIR, cmd=["./test"], allow_failure=False)
        mock_request = Mock()
        mock_factory.return_value = mock_request
        
        result = builder._step_to_request(step)
        
        assert result == mock_request
        mock_factory.assert_called_once_with(step, context=None)
    
    @patch('src.env_core.workflow.pure_request_factory.PureRequestFactory.create_request_from_step')
    def test_step_to_request_failure(self, mock_factory, builder):
        """StepからRequest生成失敗テスト"""
        step = Step(type=StepType.BUILD, cmd=["make"], allow_failure=False)  # 未対応タイプ
        mock_factory.return_value = None
        
        result = builder._step_to_request(step)
        
        assert result is None
        mock_factory.assert_called_once_with(step, context=None)
    
    def test_extract_resource_info_from_step(self, builder):
        """Stepからのリソース情報抽出テスト"""
        # mkdir step
        mkdir_step = Step(type=StepType.MKDIR, cmd=["./test_dir"], allow_failure=False)
        creates_files, creates_dirs, reads_files, requires_dirs = \
            builder._extract_resource_info_from_step(mkdir_step)
        
        assert "./test_dir" in creates_dirs
        assert len(creates_files) == 0
        
        # copy step  
        copy_step = Step(type=StepType.COPY, cmd=["./src.txt", "./dst.txt"], allow_failure=False)
        creates_files, creates_dirs, reads_files, requires_dirs = \
            builder._extract_resource_info_from_step(copy_step)
        
        assert "./src.txt" in reads_files
        assert "./dst.txt" in creates_files
    
    def test_operations_independence(self, step_context):
        """operations非依存の確認テスト"""
        # operationsを渡さずにビルダー作成
        builder = GraphBasedWorkflowBuilder.from_context(step_context)
        
        json_steps = [{"type": "mkdir", "cmd": ["./test"]}]
        
        # operations非依存で動作することを確認
        # 実際の動作は依存するモジュールのimportによるが、
        # 少なくともビルダー自体はoperationsを要求しない
        assert builder.context == step_context
        assert not hasattr(builder, 'operations')  # operationsフィールドなし
    
    def test_backward_compatibility_from_controller(self):
        """既存のfrom_controllerメソッドの互換性テスト"""
        mock_controller = Mock()
        mock_controller.env_context = Mock()
        mock_controller.env_context.contest_name = "test"
        mock_controller.env_context.problem_name = "problem"
        mock_controller.env_context.language = "python"
        mock_controller.env_context.env_type = "local"
        mock_controller.env_context.command_type = "run"
        
        mock_operations = Mock()
        
        with patch('src.env_core.step.workflow.create_step_context_from_env_context') as mock_create:
            mock_context = Mock()
            mock_create.return_value = mock_context
            
            builder = GraphBasedWorkflowBuilder.from_controller(mock_controller, mock_operations)
            
            assert builder.context == mock_context
            mock_create.assert_called_once_with(mock_controller.env_context)