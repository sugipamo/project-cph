"""
Tests for GraphBasedWorkflowBuilder
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from src.env_core.workflow.graph_based_workflow_builder import GraphBasedWorkflowBuilder
from src.env_core.workflow.request_execution_graph import RequestExecutionGraph, RequestNode
from src.env_core.step.step import Step, StepType, StepContext, StepGenerationResult
from src.context.resolver.config_node import ConfigNode
from src.operations.composite.composite_request import CompositeRequest


class TestGraphBasedWorkflowBuilder:
    
    def test_init(self):
        """Test GraphBasedWorkflowBuilder initialization"""
        context = Mock(spec=StepContext)
        builder = GraphBasedWorkflowBuilder(context)
        
        assert builder.context == context
    
    def test_from_context(self):
        """Test creating builder from context"""
        context = Mock(spec=StepContext)
        builder = GraphBasedWorkflowBuilder.from_context(context)
        
        assert isinstance(builder, GraphBasedWorkflowBuilder)
        assert builder.context == context
    
    @patch('src.env_core.step.workflow.create_step_context_from_env_context')
    def test_from_controller(self, mock_create_context):
        """Test creating builder from controller"""
        # Setup
        controller = Mock()
        controller.env_context = Mock()
        operations = Mock()
        
        step_context = Mock(spec=StepContext)
        mock_create_context.return_value = step_context
        
        # Execute
        builder = GraphBasedWorkflowBuilder.from_controller(controller, operations)
        
        # Verify
        assert isinstance(builder, GraphBasedWorkflowBuilder)
        assert builder.context is step_context
        mock_create_context.assert_called_once_with(controller.env_context)
    
    @patch('src.env_core.workflow.graph_based_workflow_builder.generate_steps_from_json')
    @patch('src.env_core.workflow.graph_based_workflow_builder.resolve_dependencies')
    @patch('src.env_core.workflow.graph_based_workflow_builder.optimize_workflow_steps')
    def test_build_graph_from_json_steps_success(self, mock_optimize, mock_resolve, mock_generate):
        """Test successful graph building from JSON steps"""
        # Setup
        json_steps = [{"type": "shell", "cmd": ["echo", "test"]}]
        context = Mock(spec=StepContext)
        builder = GraphBasedWorkflowBuilder(context)
        
        # Mock step generation
        test_step = Mock(spec=Step)
        test_step.type = StepType.SHELL
        test_step.cmd = ["echo", "test"]
        
        generation_result = Mock(spec=StepGenerationResult)
        generation_result.is_success = True
        generation_result.steps = [test_step]
        generation_result.errors = []
        generation_result.warnings = ["Test warning"]
        mock_generate.return_value = generation_result
        
        # Mock dependency resolution and optimization
        mock_resolve.return_value = [test_step]
        mock_optimize.return_value = [test_step]
        
        # Mock _build_graph_from_steps
        mock_graph = Mock(spec=RequestExecutionGraph)
        with patch.object(builder, '_build_graph_from_steps', return_value=mock_graph):
            # Execute
            graph, errors, warnings = builder.build_graph_from_json_steps(json_steps)
        
        # Verify
        assert graph == mock_graph
        assert errors == []
        assert warnings == ["Test warning"]
        
        mock_generate.assert_called_once_with(json_steps, context)
        mock_resolve.assert_called_once_with([test_step], context)
        mock_optimize.assert_called_once_with([test_step])
    
    @patch('src.env_core.workflow.graph_based_workflow_builder.generate_steps_from_json')
    def test_build_graph_from_json_steps_failure(self, mock_generate):
        """Test graph building with step generation failure"""
        # Setup
        json_steps = [{"type": "invalid"}]
        builder = GraphBasedWorkflowBuilder()  # No context
        
        # Mock failed generation
        generation_result = Mock(spec=StepGenerationResult)
        generation_result.is_success = False
        generation_result.errors = ["Invalid step type"]
        generation_result.warnings = []
        mock_generate.return_value = generation_result
        
        # Execute
        graph, errors, warnings = builder.build_graph_from_json_steps(json_steps)
        
        # Verify
        assert isinstance(graph, RequestExecutionGraph)
        assert errors == ["Invalid step type"]
        assert warnings == []
    
    @patch('src.env_core.step.step.StepContext')
    @patch('src.env_core.workflow.graph_based_workflow_builder.generate_steps_from_json')
    def test_build_graph_with_default_context(self, mock_generate, mock_step_context_class):
        """Test graph building with default context when none provided"""
        # Setup
        builder = GraphBasedWorkflowBuilder()  # No context
        json_steps = [{"type": "shell", "cmd": ["ls"]}]
        
        # Mock default context creation
        default_context = Mock(spec=StepContext)
        mock_step_context_class.return_value = default_context
        
        # Mock successful generation
        generation_result = Mock(spec=StepGenerationResult)
        generation_result.is_success = True
        generation_result.steps = []
        generation_result.errors = []
        generation_result.warnings = []
        mock_generate.return_value = generation_result
        
        # Execute
        graph, errors, warnings = builder.build_graph_from_json_steps(json_steps)
        
        # Verify default context was created
        mock_step_context_class.assert_called_once_with(
            contest_name="",
            problem_name="",
            language="",
            env_type="local",
            command_type="",
            workspace_path="./workspace",
            contest_current_path="./contest_current"
        )
        mock_generate.assert_called_once_with(json_steps, default_context)
    
    def test_build_graph_from_nodes(self):
        """Test building graph from ConfigNodes"""
        # Setup
        builder = GraphBasedWorkflowBuilder()
        
        # Create ConfigNodes
        node1 = Mock(spec=ConfigNode)
        node1.value = {"type": "shell", "cmd": ["echo", "1"]}
        
        node2 = Mock(spec=ConfigNode)
        node2.value = {"type": "copy", "cmd": ["src", "dst"]}
        
        node3 = Mock(spec=ConfigNode)
        node3.value = None  # Invalid node
        
        step_nodes = [node1, node2, node3]
        
        # Mock build_graph_from_json_steps
        mock_graph = Mock(spec=RequestExecutionGraph)
        with patch.object(builder, 'build_graph_from_json_steps', 
                         return_value=(mock_graph, [], [])) as mock_build:
            # Execute
            graph, errors, warnings = builder.build_graph_from_nodes(step_nodes)
        
        # Verify
        assert graph == mock_graph
        # Should only pass valid nodes
        expected_json = [
            {"type": "shell", "cmd": ["echo", "1"]},
            {"type": "copy", "cmd": ["src", "dst"]}
        ]
        mock_build.assert_called_once_with(expected_json)
    
    @patch('src.env_core.workflow.graph_based_workflow_builder.GraphToCompositeAdapter')
    def test_build_composite_from_graph(self, mock_adapter_class):
        """Test building CompositeRequest from graph"""
        # Setup
        builder = GraphBasedWorkflowBuilder()
        mock_graph = Mock(spec=RequestExecutionGraph)
        mock_composite = Mock(spec=CompositeRequest)
        
        mock_adapter_class.to_composite_request.return_value = mock_composite
        
        # Execute
        result = builder.build_composite_from_graph(mock_graph)
        
        # Verify
        assert result == mock_composite
        mock_adapter_class.to_composite_request.assert_called_once_with(mock_graph)
    
    def test_build_graph_from_steps(self):
        """Test building graph from steps"""
        # Setup
        context = Mock(spec=StepContext)
        context.env_json = None
        builder = GraphBasedWorkflowBuilder(context)
        
        # Create test steps
        step1 = Mock(spec=Step)
        step1.type = StepType.MKDIR
        step1.cmd = ["./output"]
        
        step2 = Mock(spec=Step)
        step2.type = StepType.SHELL
        step2.cmd = ["echo", "test"]
        
        steps = [step1, step2]
        
        # Mock helper methods
        mock_request1 = Mock()
        mock_request2 = Mock()
        
        with patch.object(builder, '_step_to_request', side_effect=[mock_request1, mock_request2]):
            with patch.object(builder, '_extract_resource_info_from_step', 
                            return_value=([], [], [], [])):
                with patch.object(builder, '_build_dependencies', return_value=None):
                    # Execute
                    graph = builder._build_graph_from_steps(steps)
        
        # Verify
        assert isinstance(graph, RequestExecutionGraph)
        # Graph should have 2 nodes
        assert len(graph.nodes) == 2
        assert graph.nodes["step_0"].request == mock_request1
        assert graph.nodes["step_1"].request == mock_request2
    
    def test_build_graph_with_debug_config(self):
        """Test building graph with debug configuration"""
        # Setup
        context = Mock(spec=StepContext)
        context.language = "python"
        context.env_json = {
            "python": {
                "debug": {"enabled": True, "level": "detailed"}
            }
        }
        builder = GraphBasedWorkflowBuilder(context)
        
        # Create a simple step
        step = Mock(spec=Step)
        step.type = StepType.SHELL
        step.cmd = ["ls"]
        
        with patch.object(builder, '_step_to_request', return_value=Mock()):
            with patch.object(builder, '_extract_resource_info_from_step', 
                            return_value=([], [], [], [])):
                with patch.object(builder, '_build_dependencies', return_value=None):
                    # Execute
                    graph = builder._build_graph_from_steps([step])
        
        # Verify debug config was passed to graph
        assert graph.debug_logger.config == {"enabled": True, "level": "detailed"}