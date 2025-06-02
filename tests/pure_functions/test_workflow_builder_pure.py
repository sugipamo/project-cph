"""
Tests for pure function workflow builder
These tests don't use mocks - they test actual behavior
"""
import pytest
from src.pure_functions.workflow_builder_pure import (
    WorkflowBuildInput,
    WorkflowBuildOutput,
    build_workflow_pure,
    parse_json_steps_pure,
    resolve_dependencies_pure,
    optimize_steps_pure,
    extract_step_resources_pure,
    extract_directory_pure,
    analyze_dependencies_pure,
    StepResources
)
from src.env_core.step.step import Step, StepType, StepContext
from src.env_core.workflow.request_execution_graph import RequestNode


class TestBuildWorkflowPure:
    """Test the main workflow building function"""
    
    def test_simple_workflow(self):
        """Test building a simple workflow"""
        # Prepare input
        json_steps = [
            {"type": "mkdir", "cmd": ["./output"]},
            {"type": "shell", "cmd": ["echo", "Hello"]}
        ]
        context = StepContext(
            contest_name="test",
            problem_name="a",
            language="python",
            env_type="local",
            command_type="build",
            workspace_path="./workspace",
            contest_current_path="./current"
        )
        input_data = WorkflowBuildInput(
            json_steps=json_steps,
            context=context
        )
        
        # Execute
        output = build_workflow_pure(input_data)
        
        # Verify
        assert isinstance(output, WorkflowBuildOutput)
        assert len(output.nodes) == 2
        assert output.nodes[0].metadata['step_type'] == 'mkdir'
        assert output.nodes[1].metadata['step_type'] == 'shell'
        assert output.errors == []
        assert output.warnings == []
        assert output.edges == []  # No dependencies in this simple case
    
    def test_workflow_with_dependencies(self):
        """Test workflow with file dependencies"""
        json_steps = [
            {"type": "touch", "cmd": ["./data.txt"]},
            {"type": "copy", "cmd": ["./data.txt", "./output/data.txt"]}
        ]
        context = StepContext(
            contest_name="test",
            problem_name="a",
            language="python",
            env_type="local",
            command_type="build",
            workspace_path="./workspace",
            contest_current_path="./current"
        )
        input_data = WorkflowBuildInput(
            json_steps=json_steps,
            context=context
        )
        
        # Execute
        output = build_workflow_pure(input_data)
        
        # Verify - should have added mkdir step
        assert len(output.nodes) >= 3
        # Should have edge from mkdir to copy (mkdir is added before copy)
        # The exact indices depend on optimization, so just check that edges exist
        assert len(output.edges) > 0
    
    def test_workflow_with_errors(self):
        """Test workflow with invalid steps"""
        json_steps = [
            {"type": "invalid_type", "cmd": ["test"]},
            {"cmd": ["no_type"]}
        ]
        context = StepContext(
            contest_name="test",
            problem_name="a",
            language="python",
            env_type="local",
            command_type="build",
            workspace_path="./workspace",
            contest_current_path="./current"
        )
        input_data = WorkflowBuildInput(
            json_steps=json_steps,
            context=context
        )
        
        # Execute
        output = build_workflow_pure(input_data)
        
        # Verify
        assert output.nodes == []
        assert len(output.errors) >= 2
        assert "invalid type" in output.errors[0]
        assert "missing 'type'" in output.errors[1]


class TestParseJsonStepsPure:
    """Test JSON parsing function"""
    
    def test_parse_valid_steps(self):
        """Test parsing valid JSON steps"""
        json_steps = [
            {
                "type": "shell",
                "cmd": ["echo", "test"],
                "allow_failure": True,
                "show_output": True
            },
            {
                "type": "copy",
                "cmd": ["src.txt", "dst.txt"]
            }
        ]
        context = StepContext(
            contest_name="test",
            problem_name="a",
            language="python",
            env_type="local",
            command_type="build",
            workspace_path="./workspace",
            contest_current_path="./current"
        )
        
        # Execute
        result = parse_json_steps_pure(json_steps, context)
        
        # Verify
        assert len(result.steps) == 2
        assert result.steps[0].type == StepType.SHELL
        assert result.steps[0].cmd == ["echo", "test"]
        assert result.steps[0].allow_failure is True
        assert result.steps[0].show_output is True
        assert result.steps[1].type == StepType.COPY
        assert result.errors == []
    
    def test_parse_invalid_steps(self):
        """Test parsing invalid steps"""
        json_steps = [
            {"type": ""},  # Empty type
            {"no_type": "shell"},  # Missing type
            {"type": "unknown_type", "cmd": []}  # Invalid type
        ]
        context = StepContext(
            contest_name="test",
            problem_name="a",
            language="python",
            env_type="local",
            command_type="build",
            workspace_path="./workspace",
            contest_current_path="./current"
        )
        
        # Execute
        result = parse_json_steps_pure(json_steps, context)
        
        # Verify
        assert len(result.steps) == 0
        assert len(result.errors) == 3


class TestResolveDependenciesPure:
    """Test dependency resolution"""
    
    def test_add_mkdir_for_file_operations(self):
        """Test that mkdir steps are added for file operations"""
        steps = [
            Step(type=StepType.TOUCH, cmd=["./output/file.txt"]),
            Step(type=StepType.COPY, cmd=["src.txt", "./data/dst.txt"])
        ]
        context = StepContext(
            contest_name="test",
            problem_name="a",
            language="python",
            env_type="local",
            command_type="build",
            workspace_path="./workspace",
            contest_current_path="./current"
        )
        
        # Execute
        resolved = resolve_dependencies_pure(steps, context)
        
        # Verify
        assert len(resolved) == 4  # 2 original + 2 mkdir
        assert resolved[0].type == StepType.MKDIR
        assert resolved[0].cmd == ["./output"]
        assert resolved[2].type == StepType.MKDIR
        assert resolved[2].cmd == ["./data"]
    
    def test_no_mkdir_for_root_files(self):
        """Test that no mkdir is added for root-level files"""
        steps = [
            Step(type=StepType.TOUCH, cmd=["file.txt"])  # No directory
        ]
        context = StepContext(
            contest_name="test",
            problem_name="a",
            language="python",
            env_type="local",
            command_type="build",
            workspace_path="./workspace",
            contest_current_path="./current"
        )
        
        # Execute
        resolved = resolve_dependencies_pure(steps, context)
        
        # Verify
        assert len(resolved) == 1  # No mkdir added


class TestOptimizeStepsPure:
    """Test step optimization"""
    
    def test_remove_duplicate_mkdirs(self):
        """Test removal of duplicate mkdir steps"""
        steps = [
            Step(type=StepType.MKDIR, cmd=["./output"]),
            Step(type=StepType.SHELL, cmd=["echo", "test"]),
            Step(type=StepType.MKDIR, cmd=["./output"])  # Duplicate
        ]
        
        # Execute
        optimized = optimize_steps_pure(steps)
        
        # Verify
        assert len(optimized) == 2
        assert optimized[0].type == StepType.MKDIR
        assert optimized[1].type == StepType.SHELL


class TestExtractStepResourcesPure:
    """Test resource extraction"""
    
    def test_touch_resources(self):
        """Test resource extraction for touch step"""
        step = Step(type=StepType.TOUCH, cmd=["./output/file.txt"])
        
        resources = extract_step_resources_pure(step)
        
        assert resources.creates_files == ["./output/file.txt"]
        assert resources.creates_dirs == []
        assert resources.reads_files == []
        assert resources.requires_dirs == ["./output"]
    
    def test_copy_resources(self):
        """Test resource extraction for copy step"""
        step = Step(type=StepType.COPY, cmd=["src.txt", "./output/dst.txt"])
        
        resources = extract_step_resources_pure(step)
        
        assert resources.creates_files == ["./output/dst.txt"]
        assert resources.creates_dirs == []
        assert resources.reads_files == ["src.txt"]
        assert resources.requires_dirs == ["./output"]
    
    def test_mkdir_resources(self):
        """Test resource extraction for mkdir step"""
        step = Step(type=StepType.MKDIR, cmd=["./output"])
        
        resources = extract_step_resources_pure(step)
        
        assert resources.creates_files == []
        assert resources.creates_dirs == ["./output"]
        assert resources.reads_files == []
        assert resources.requires_dirs == []


class TestExtractDirectoryPure:
    """Test directory extraction"""
    
    def test_extract_directory_from_path(self):
        """Test extracting directory from file path"""
        assert extract_directory_pure("./output/file.txt") == "./output"
        assert extract_directory_pure("./a/b/c/file.txt") == "./a/b/c"
        assert extract_directory_pure("file.txt") is None
        assert extract_directory_pure("") is None
        assert extract_directory_pure("/abs/path/file.txt") == "/abs/path"


class TestAnalyzeDependenciesPure:
    """Test dependency analysis"""
    
    def test_file_dependency(self):
        """Test detecting file dependencies"""
        nodes = [
            RequestNode(
                id="step_0",
                request=None,
                creates_files=["data.txt"],
                creates_dirs=[],
                reads_files=[],
                requires_dirs=[]
            ),
            RequestNode(
                id="step_1",
                request=None,
                creates_files=[],
                creates_dirs=[],
                reads_files=["data.txt"],
                requires_dirs=[]
            )
        ]
        
        edges = analyze_dependencies_pure(nodes)
        
        assert edges == [("step_0", "step_1")]
    
    def test_directory_dependency(self):
        """Test detecting directory dependencies"""
        nodes = [
            RequestNode(
                id="step_0",
                request=None,
                creates_files=[],
                creates_dirs=["./output"],
                reads_files=[],
                requires_dirs=[]
            ),
            RequestNode(
                id="step_1",
                request=None,
                creates_files=[],
                creates_dirs=[],
                reads_files=[],
                requires_dirs=["./output"]
            )
        ]
        
        edges = analyze_dependencies_pure(nodes)
        
        assert edges == [("step_0", "step_1")]
    
    def test_no_self_edges(self):
        """Test that self-edges are not created"""
        nodes = [
            RequestNode(
                id="step_0",
                request=None,
                creates_files=["data.txt"],
                creates_dirs=[],
                reads_files=["data.txt"],  # Reading own output
                requires_dirs=[]
            )
        ]
        
        edges = analyze_dependencies_pure(nodes)
        
        assert edges == []  # No self-edge