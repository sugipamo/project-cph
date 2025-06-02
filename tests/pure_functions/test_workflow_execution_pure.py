"""
Tests for pure workflow execution functions
"""
import pytest
from src.pure_functions.workflow_execution_pure import (
    WorkflowConfig,
    WorkflowPlan,
    WorkflowTask,
    extract_workflow_config_pure,
    plan_workflow_execution_pure,
    analyze_preparation_needs_pure,
    create_workflow_tasks_pure,
    validate_workflow_plan_pure,
    has_circular_dependencies_pure,
    optimize_workflow_plan_pure
)
from src.pure_functions.execution_context_pure import ExecutionData, StepContextData
from src.env_core.step.step import Step, StepType


class TestWorkflowConfigExtraction:
    """Test workflow configuration extraction"""
    
    def test_extract_valid_config(self):
        """Test extracting valid workflow configuration"""
        data = ExecutionData(
            command_type="build",
            language="python",
            contest_name="abc123",
            problem_name="a",
            env_type="docker",
            env_json={
                "python": {
                    "commands": {
                        "build": {
                            "steps": [
                                {"type": "shell", "cmd": ["echo", "build"]}
                            ]
                        }
                    },
                    "debug": {"enabled": True}
                }
            }
        )
        
        config = extract_workflow_config_pure(data)
        
        assert config is not None
        assert len(config.steps) == 1
        assert config.language == "python"
        assert config.command_type == "build"
        assert config.env_type == "docker"
        assert config.debug_config == {"enabled": True}
    
    def test_extract_no_env_json(self):
        """Test extraction with no env_json"""
        data = ExecutionData(
            command_type="build",
            language="python",
            contest_name="abc123",
            problem_name="a",
            env_type="docker",
            env_json=None
        )
        
        config = extract_workflow_config_pure(data)
        assert config is None
    
    def test_extract_no_steps(self):
        """Test extraction with no steps"""
        data = ExecutionData(
            command_type="build",
            language="python",
            contest_name="abc123",
            problem_name="a",
            env_type="docker",
            env_json={
                "python": {
                    "commands": {
                        "build": {}
                    }
                }
            }
        )
        
        config = extract_workflow_config_pure(data)
        assert config is None


class TestWorkflowPlanning:
    """Test workflow planning"""
    
    def test_plan_simple_workflow(self):
        """Test planning a simple workflow"""
        config = WorkflowConfig(
            steps=[
                {"type": "mkdir", "cmd": ["./output"]},
                {"type": "shell", "cmd": ["echo", "test"]}
            ],
            language="python",
            command_type="build",
            env_type="local"
        )
        
        context = StepContextData(
            contest_name="abc123",
            problem_name="a",
            language="python",
            env_type="local",
            command_type="build",
            workspace_path="./workspace",
            contest_current_path="./current"
        )
        
        plan = plan_workflow_execution_pure(config, context)
        
        assert isinstance(plan, WorkflowPlan)
        assert len(plan.main_steps) == 2
        assert plan.main_steps[0].type == StepType.MKDIR
        assert plan.main_steps[1].type == StepType.SHELL
        assert plan.errors == []
        assert plan.preparation_steps == []
    
    def test_plan_with_dependencies(self):
        """Test planning workflow with dependencies"""
        config = WorkflowConfig(
            steps=[
                {"type": "touch", "cmd": ["data.txt"]},
                {"type": "copy", "cmd": ["data.txt", "./output/data.txt"]}
            ],
            language="python",
            command_type="build",
            env_type="local"
        )
        
        context = StepContextData(
            contest_name="abc123",
            problem_name="a",
            language="python",
            env_type="local",
            command_type="build",
            workspace_path="./workspace",
            contest_current_path="./current"
        )
        
        plan = plan_workflow_execution_pure(config, context)
        
        # Should have added mkdir step
        assert len(plan.main_steps) >= 3
        # Should have dependencies
        assert len(plan.dependencies) > 0
    
    def test_plan_with_errors(self):
        """Test planning with invalid steps"""
        config = WorkflowConfig(
            steps=[
                {"type": "invalid_type", "cmd": ["test"]}
            ],
            language="python",
            command_type="build",
            env_type="local"
        )
        
        context = StepContextData(
            contest_name="abc123",
            problem_name="a",
            language="python",
            env_type="local",
            command_type="build",
            workspace_path="./workspace",
            contest_current_path="./current"
        )
        
        plan = plan_workflow_execution_pure(config, context)
        
        assert plan.main_steps == []
        assert len(plan.errors) > 0


class TestPreparationAnalysis:
    """Test preparation needs analysis"""
    
    def test_docker_preparation_needed(self):
        """Test Docker preparation detection"""
        steps = [
            Step(type=StepType.DOCKER_RUN, cmd=["ubuntu:latest"]),
            Step(type=StepType.DOCKER_EXEC, cmd=["container", "ls"])
        ]
        
        prep_steps = analyze_preparation_needs_pure(steps, "docker")
        
        assert len(prep_steps) > 0
        assert prep_steps[0].type == StepType.SHELL
        assert "docker" in prep_steps[0].cmd
    
    def test_no_preparation_for_local(self):
        """Test no preparation needed for local environment"""
        steps = [
            Step(type=StepType.SHELL, cmd=["echo", "test"])
        ]
        
        prep_steps = analyze_preparation_needs_pure(steps, "local")
        
        assert prep_steps == []


class TestWorkflowTaskCreation:
    """Test workflow task creation"""
    
    def test_create_file_tasks(self):
        """Test creating file operation tasks"""
        steps = [
            Step(type=StepType.MKDIR, cmd=["./output"]),
            Step(type=StepType.TOUCH, cmd=["file.txt"]),
            Step(type=StepType.COPY, cmd=["src", "dst"])
        ]
        
        tasks = create_workflow_tasks_pure(steps, "local")
        
        assert len(tasks) == 3
        assert all(task.request_type == "file" for task in tasks)
        assert not any(task.requires_preparation for task in tasks)
    
    def test_create_docker_tasks(self):
        """Test creating Docker tasks"""
        steps = [
            Step(type=StepType.DOCKER_RUN, cmd=["ubuntu"]),
            Step(type=StepType.DOCKER_EXEC, cmd=["container", "ls"])
        ]
        
        tasks = create_workflow_tasks_pure(steps, "docker")
        
        assert len(tasks) == 2
        assert all(task.request_type == "docker" for task in tasks)
        assert tasks[1].requires_preparation  # exec needs preparation
        assert tasks[1].preparation_info["container_check"]
    
    def test_create_mixed_tasks(self):
        """Test creating mixed type tasks"""
        steps = [
            Step(type=StepType.SHELL, cmd=["echo"]),
            Step(type=StepType.PYTHON, cmd=["print('hi')"]),
            Step(type=StepType.MKDIR, cmd=["dir"])
        ]
        
        tasks = create_workflow_tasks_pure(steps, "local")
        
        assert tasks[0].request_type == "shell"
        assert tasks[1].request_type == "python"
        assert tasks[2].request_type == "file"


class TestWorkflowValidation:
    """Test workflow plan validation"""
    
    def test_validate_valid_plan(self):
        """Test validation of valid plan"""
        plan = WorkflowPlan(
            main_steps=[
                Step(type=StepType.SHELL, cmd=["echo", "test"])
            ],
            preparation_steps=[],
            dependencies=[]
        )
        
        errors = validate_workflow_plan_pure(plan)
        assert errors == []
    
    def test_validate_empty_workflow(self):
        """Test validation of empty workflow"""
        plan = WorkflowPlan(
            main_steps=[],
            preparation_steps=[],
            dependencies=[]
        )
        
        errors = validate_workflow_plan_pure(plan)
        assert "Workflow has no steps to execute" in errors
    
    def test_validate_existing_errors(self):
        """Test validation with existing errors"""
        plan = WorkflowPlan(
            main_steps=[],
            preparation_steps=[],
            dependencies=[],
            errors=["Existing error"]
        )
        
        errors = validate_workflow_plan_pure(plan)
        assert errors == ["Existing error"]
    
    def test_validate_empty_commands(self):
        """Test validation of steps with empty commands"""
        # Note: Step validation prevents empty commands, so we test the validator logic
        # by directly creating a plan with "conceptually" empty commands
        from unittest.mock import Mock
        
        mock_step = Mock()
        mock_step.type = StepType.SHELL
        mock_step.cmd = []  # Mock allows empty cmd
        
        plan = WorkflowPlan(
            main_steps=[mock_step],
            preparation_steps=[],
            dependencies=[]
        )
        
        errors = validate_workflow_plan_pure(plan)
        assert any("empty command" in e for e in errors)
    
    def test_validate_circular_dependencies(self):
        """Test validation of circular dependencies"""
        plan = WorkflowPlan(
            main_steps=[
                Step(type=StepType.SHELL, cmd=["echo", "1"]),
                Step(type=StepType.SHELL, cmd=["echo", "2"])
            ],
            preparation_steps=[],
            dependencies=[(0, 1), (1, 0)]  # Circular
        )
        
        errors = validate_workflow_plan_pure(plan)
        assert "circular dependencies" in errors[0]


class TestCircularDependencyDetection:
    """Test circular dependency detection"""
    
    def test_no_dependencies(self):
        """Test with no dependencies"""
        assert not has_circular_dependencies_pure(5, [])
    
    def test_linear_dependencies(self):
        """Test with linear dependencies"""
        edges = [(0, 1), (1, 2), (2, 3)]
        assert not has_circular_dependencies_pure(4, edges)
    
    def test_simple_cycle(self):
        """Test with simple cycle"""
        edges = [(0, 1), (1, 2), (2, 0)]
        assert has_circular_dependencies_pure(3, edges)
    
    def test_self_loop(self):
        """Test with self loop"""
        edges = [(0, 0)]
        assert has_circular_dependencies_pure(1, edges)
    
    def test_complex_graph_with_cycle(self):
        """Test complex graph with cycle"""
        edges = [
            (0, 1), (0, 2),
            (1, 3), (2, 3),
            (3, 4), (4, 2)  # Cycle: 2->3->4->2
        ]
        assert has_circular_dependencies_pure(5, edges)
    
    def test_disconnected_components(self):
        """Test with disconnected components"""
        edges = [
            (0, 1),  # Component 1
            (2, 3)   # Component 2
        ]
        assert not has_circular_dependencies_pure(4, edges)


class TestWorkflowOptimization:
    """Test workflow plan optimization"""
    
    def test_remove_duplicate_preparation(self):
        """Test removal of duplicate preparation steps"""
        plan = WorkflowPlan(
            main_steps=[
                Step(type=StepType.SHELL, cmd=["echo", "test"])
            ],
            preparation_steps=[
                Step(type=StepType.SHELL, cmd=["docker", "ps"]),
                Step(type=StepType.SHELL, cmd=["docker", "ps"]),  # Duplicate
                Step(type=StepType.SHELL, cmd=["docker", "images"])
            ],
            dependencies=[]
        )
        
        optimized = optimize_workflow_plan_pure(plan)
        
        assert len(optimized.preparation_steps) == 2
        assert optimized.main_steps == plan.main_steps
    
    def test_no_optimization_with_errors(self):
        """Test no optimization when errors exist"""
        plan = WorkflowPlan(
            main_steps=[],
            preparation_steps=[
                Step(type=StepType.SHELL, cmd=["cmd1"]),
                Step(type=StepType.SHELL, cmd=["cmd1"])  # Duplicate
            ],
            dependencies=[],
            errors=["Error"]
        )
        
        optimized = optimize_workflow_plan_pure(plan)
        
        # Should not optimize when errors exist
        assert optimized == plan