"""
Tests for GraphBasedWorkflowBuilder
"""
from unittest.mock import MagicMock, Mock, patch

import pytest

from src.context.resolver.config_node import ConfigNode
from src.domain.requests.composite.composite_request import CompositeRequest
from src.workflow.step.step import Step, StepContext, StepGenerationResult, StepType
from src.workflow.workflow.graph_based_workflow_builder import GraphBasedWorkflowBuilder
from src.workflow.workflow.request_execution_graph import RequestExecutionGraph, RequestNode


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

    @patch('src.workflow.workflow.graph_based_workflow_builder.create_step_context_from_env_context')
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

    @patch('src.workflow.workflow.graph_based_workflow_builder.generate_steps_from_json')
    @patch('src.workflow.workflow.graph_based_workflow_builder.resolve_dependencies')
    @patch('src.workflow.workflow.graph_based_workflow_builder.optimize_workflow_steps')
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

    @patch('src.workflow.workflow.graph_based_workflow_builder.generate_steps_from_json')
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

    @patch('src.workflow.step.step.StepContext')
    @patch('src.workflow.workflow.graph_based_workflow_builder.generate_steps_from_json')
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

    def test_build_graph_pure_method(self):
        """Test pure function based graph building"""
        # Setup
        context = Mock(spec=StepContext)
        context.env_json = None
        builder = GraphBasedWorkflowBuilder(context)

        # Create test steps
        step1 = Step(type=StepType.MKDIR, cmd=["./output"])
        step2 = Step(type=StepType.TOUCH, cmd=["./output/file.txt"])
        steps = [step1, step2]

        # Mock the step to request conversion
        with patch.object(builder, '_step_to_request', side_effect=[Mock(), Mock()]):
            # Execute
            graph, errors, warnings = builder.build_graph_pure(steps)

        # Verify
        assert isinstance(graph, RequestExecutionGraph)
        assert len(graph.nodes) == 2
        assert len(errors) == 0
        assert "step_0" in graph.nodes
        assert "step_1" in graph.nodes

    def test_extract_resource_info_integration(self):
        """Test resource info extraction using pure functions"""
        # Setup
        builder = GraphBasedWorkflowBuilder()

        # Test different step types
        mkdir_step = Step(type=StepType.MKDIR, cmd=["./test"])
        touch_step = Step(type=StepType.TOUCH, cmd=["./test/file.txt"])
        copy_step = Step(type=StepType.COPY, cmd=["src.txt", "./test/dst.txt"])

        # Execute
        mkdir_result = builder._extract_resource_info_from_step(mkdir_step)
        touch_result = builder._extract_resource_info_from_step(touch_step)
        copy_result = builder._extract_resource_info_from_step(copy_step)

        # Verify
        assert mkdir_result[1] == {"./test"}  # creates_dirs
        assert touch_result[0] == {"./test/file.txt"}  # creates_files
        assert copy_result[0] == {"./test/dst.txt"}  # creates_files
        assert copy_result[2] == {"src.txt"}  # reads_files

    def test_parent_directory_check_integration(self):
        """Test parent directory checking using pure functions"""
        builder = GraphBasedWorkflowBuilder()

        # Test cases
        assert builder._is_parent_directory("./output", "./output/subdir")
        assert not builder._is_parent_directory("./output", "./other")
        assert not builder._is_parent_directory("./output/subdir", "./output")

    def test_resource_conflict_check_integration(self):
        """Test resource conflict checking using pure functions"""
        builder = GraphBasedWorkflowBuilder()

        # Create conflicting nodes
        node1 = Mock(spec=RequestNode)
        node1.id = "node1"
        node1.creates_files = {"test.txt"}
        node1.creates_dirs = set()
        node1.reads_files = set()
        node1.requires_dirs = set()

        node2 = Mock(spec=RequestNode)
        node2.id = "node2"
        node2.creates_files = {"test.txt"}  # Same file - conflict
        node2.creates_dirs = set()
        node2.reads_files = set()
        node2.requires_dirs = set()

        node3 = Mock(spec=RequestNode)
        node3.id = "node3"
        node3.creates_files = {"other.txt"}  # Different file - no conflict
        node3.creates_dirs = set()
        node3.reads_files = set()
        node3.requires_dirs = set()

        # Test conflict detection
        assert builder._has_resource_conflict(node1, node2)  # Should have conflict
        assert not builder._has_resource_conflict(node1, node3)  # Should not have conflict
