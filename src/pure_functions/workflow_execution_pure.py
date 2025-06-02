"""
Pure function implementation of workflow execution logic
"""
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Tuple
from src.pure_functions.execution_context_pure import ExecutionData, StepContextData
from src.pure_functions.workflow_builder_pure import WorkflowBuildInput, build_workflow_pure
from src.env_core.step.step import Step, StepType, StepContext


@dataclass(frozen=True)
class WorkflowConfig:
    """Configuration for workflow execution"""
    steps: List[Dict[str, Any]]
    language: str
    command_type: str
    env_type: str
    debug_config: Optional[Dict[str, Any]] = None


@dataclass(frozen=True)
class WorkflowPlan:
    """
    Complete workflow execution plan
    This is the output of planning phase, before any execution
    """
    main_steps: List[Step]
    preparation_steps: List[Step]
    dependencies: List[Tuple[int, int]]  # (from_index, to_index)
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


@dataclass(frozen=True)
class WorkflowTask:
    """A single task in the workflow"""
    step: Step
    request_type: str
    requires_preparation: bool = False
    preparation_info: Optional[Dict[str, Any]] = None


def extract_workflow_config_pure(
    execution_data: ExecutionData
) -> Optional[WorkflowConfig]:
    """
    Extract workflow configuration from execution data (pure function)
    
    Returns None if no valid workflow configuration found
    """
    if not execution_data.env_json:
        return None
    
    language_config = execution_data.env_json.get(execution_data.language, {})
    commands = language_config.get("commands", {})
    command_config = commands.get(execution_data.command_type, {})
    
    steps = command_config.get("steps", [])
    if not steps:
        return None
    
    debug_config = language_config.get("debug")
    
    return WorkflowConfig(
        steps=steps,
        language=execution_data.language,
        command_type=execution_data.command_type,
        env_type=execution_data.env_type,
        debug_config=debug_config
    )


def plan_workflow_execution_pure(
    workflow_config: WorkflowConfig,
    step_context: StepContextData
) -> WorkflowPlan:
    """
    Plan the complete workflow execution (pure function)
    
    This function determines:
    1. What steps need to be executed
    2. What preparation is needed
    3. Dependencies between steps
    """
    # Convert StepContextData to StepContext for compatibility
    context = StepContext(
        contest_name=step_context.contest_name,
        problem_name=step_context.problem_name,
        language=step_context.language,
        env_type=step_context.env_type,
        command_type=step_context.command_type,
        workspace_path=step_context.workspace_path,
        contest_current_path=step_context.contest_current_path,
        contest_stock_path=step_context.contest_stock_path,
        contest_template_path=step_context.contest_template_path,
        contest_temp_path=step_context.contest_temp_path,
        source_file_name=step_context.source_file_name,
        language_id=step_context.language_id
    )
    
    # Build workflow using pure function
    input_data = WorkflowBuildInput(
        json_steps=workflow_config.steps,
        context=context,
        debug_config=workflow_config.debug_config
    )
    
    output = build_workflow_pure(input_data)
    
    if output.errors:
        return WorkflowPlan(
            main_steps=[],
            preparation_steps=[],
            dependencies=[],
            errors=output.errors,
            warnings=output.warnings
        )
    
    # Convert nodes back to steps
    main_steps = []
    for node in output.nodes:
        # Reconstruct step from metadata
        step_type = StepType(node.metadata['step_type'])
        step = Step(
            type=step_type,
            cmd=node.metadata['step_cmd'],
            allow_failure=node.metadata.get('allow_failure', False),
            show_output=node.metadata.get('show_output', False)
        )
        main_steps.append(step)
    
    # Analyze which steps need preparation
    preparation_steps = analyze_preparation_needs_pure(
        main_steps,
        workflow_config.env_type
    )
    
    # Convert edges to numeric indices
    node_id_to_index = {node.id: i for i, node in enumerate(output.nodes)}
    dependencies = [
        (node_id_to_index[from_id], node_id_to_index[to_id])
        for from_id, to_id in output.edges
        if from_id in node_id_to_index and to_id in node_id_to_index
    ]
    
    return WorkflowPlan(
        main_steps=main_steps,
        preparation_steps=preparation_steps,
        dependencies=dependencies,
        errors=output.errors,
        warnings=output.warnings
    )


def analyze_preparation_needs_pure(
    steps: List[Step],
    env_type: str
) -> List[Step]:
    """
    Analyze what preparation steps are needed (pure function)
    """
    preparation_steps = []
    
    if env_type == "docker":
        # Check if we need to prepare Docker environment
        has_docker_steps = any(
            step.type in [StepType.DOCKER_RUN, StepType.DOCKER_EXEC, StepType.DOCKER_CP]
            for step in steps
        )
        
        if has_docker_steps:
            # Add Docker preparation steps
            preparation_steps.append(
                Step(
                    type=StepType.SHELL,
                    cmd=["docker", "ps", "-a"],
                    allow_failure=True
                )
            )
    
    return preparation_steps


def create_workflow_tasks_pure(
    steps: List[Step],
    env_type: str
) -> List[WorkflowTask]:
    """
    Convert steps to workflow tasks with additional metadata (pure function)
    """
    tasks = []
    
    for step in steps:
        # Determine request type
        if step.type in [StepType.DOCKER_RUN, StepType.DOCKER_EXEC, StepType.DOCKER_CP]:
            request_type = "docker"
        elif step.type in [StepType.MKDIR, StepType.TOUCH, StepType.COPY, 
                          StepType.MOVE, StepType.REMOVE, StepType.RMTREE]:
            request_type = "file"
        elif step.type == StepType.PYTHON:
            request_type = "python"
        else:
            request_type = "shell"
        
        # Check if preparation is needed
        requires_preparation = (
            env_type == "docker" and 
            request_type == "docker" and
            step.type == StepType.DOCKER_EXEC
        )
        
        task = WorkflowTask(
            step=step,
            request_type=request_type,
            requires_preparation=requires_preparation,
            preparation_info={
                "container_check": requires_preparation
            } if requires_preparation else None
        )
        
        tasks.append(task)
    
    return tasks


def validate_workflow_plan_pure(plan: WorkflowPlan) -> List[str]:
    """
    Validate a workflow plan (pure function)
    
    Returns list of validation errors
    """
    errors = []
    
    # Check for errors in plan
    if plan.errors:
        errors.extend(plan.errors)
        return errors  # No point in further validation
    
    # Check for empty workflow
    if not plan.main_steps and not plan.preparation_steps:
        errors.append("Workflow has no steps to execute")
    
    # Check for circular dependencies
    if has_circular_dependencies_pure(
        len(plan.main_steps),
        plan.dependencies
    ):
        errors.append("Workflow has circular dependencies")
    
    # Validate step configurations
    for i, step in enumerate(plan.main_steps):
        if not step.cmd:
            errors.append(f"Step {i} ({step.type.value}) has empty command")
    
    return errors


def has_circular_dependencies_pure(
    num_nodes: int,
    edges: List[Tuple[int, int]]
) -> bool:
    """
    Check if a directed graph has circular dependencies (pure function)
    
    Uses DFS to detect cycles
    """
    if not edges:
        return False
    
    # Build adjacency list
    graph = {i: [] for i in range(num_nodes)}
    for from_idx, to_idx in edges:
        if from_idx < num_nodes and to_idx < num_nodes:
            graph[from_idx].append(to_idx)
    
    # Track visit states: 0=unvisited, 1=visiting, 2=visited
    states = [0] * num_nodes
    
    def has_cycle_from(node: int) -> bool:
        if states[node] == 1:  # Currently visiting = cycle detected
            return True
        if states[node] == 2:  # Already visited
            return False
        
        states[node] = 1  # Mark as visiting
        
        # Check all neighbors
        for neighbor in graph[node]:
            if has_cycle_from(neighbor):
                return True
        
        states[node] = 2  # Mark as visited
        return False
    
    # Check all nodes
    for i in range(num_nodes):
        if states[i] == 0:  # Unvisited
            if has_cycle_from(i):
                return True
    
    return False


def optimize_workflow_plan_pure(plan: WorkflowPlan) -> WorkflowPlan:
    """
    Optimize a workflow plan (pure function)
    
    Optimizations:
    1. Remove redundant steps
    2. Merge compatible steps
    3. Identify parallelizable steps
    """
    if plan.errors:
        return plan  # Don't optimize if there are errors
    
    # For now, just remove duplicate preparation steps
    seen_prep = set()
    unique_prep = []
    
    for step in plan.preparation_steps:
        step_key = (step.type.value, tuple(step.cmd))
        if step_key not in seen_prep:
            seen_prep.add(step_key)
            unique_prep.append(step)
    
    return WorkflowPlan(
        main_steps=plan.main_steps,
        preparation_steps=unique_prep,
        dependencies=plan.dependencies,
        errors=plan.errors,
        warnings=plan.warnings
    )