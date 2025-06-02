"""
Pure function implementation of workflow building logic
"""
from typing import List, Dict, Any, Tuple, Optional, NamedTuple
from dataclasses import dataclass
from src.env_core.step.step import Step, StepType, StepContext
from src.env_core.workflow.request_execution_graph import RequestNode


@dataclass(frozen=True)
class WorkflowBuildInput:
    """Immutable input data for workflow building"""
    json_steps: List[Dict[str, Any]]
    context: StepContext
    debug_config: Optional[Dict[str, Any]] = None


@dataclass(frozen=True)
class WorkflowBuildOutput:
    """Immutable output data from workflow building"""
    nodes: List[RequestNode]
    edges: List[Tuple[str, str]]  # List of (from_id, to_id) tuples
    errors: List[str]
    warnings: List[str]


@dataclass(frozen=True)
class StepProcessingResult:
    """Result of processing a single step"""
    node: Optional[RequestNode]
    error: Optional[str]
    warning: Optional[str]


def build_workflow_pure(input_data: WorkflowBuildInput) -> WorkflowBuildOutput:
    """
    Pure function to build workflow from JSON steps
    
    This function has no side effects and always returns the same output
    for the same input.
    """
    # 1. Parse JSON steps to Step objects
    step_results = parse_json_steps_pure(input_data.json_steps, input_data.context)
    
    if step_results.errors:
        return WorkflowBuildOutput(
            nodes=[],
            edges=[],
            errors=step_results.errors,
            warnings=step_results.warnings
        )
    
    # 2. Resolve dependencies
    resolved_steps = resolve_dependencies_pure(step_results.steps, input_data.context)
    
    # 3. Optimize steps
    optimized_steps = optimize_steps_pure(resolved_steps)
    
    # 4. Convert steps to nodes
    nodes = []
    errors = list(step_results.errors)
    warnings = list(step_results.warnings)
    
    for i, step in enumerate(optimized_steps):
        result = step_to_node_pure(step, i, input_data.context)
        if result.node:
            nodes.append(result.node)
        if result.error:
            errors.append(result.error)
        if result.warning:
            warnings.append(result.warning)
    
    # 5. Analyze dependencies and create edges
    edges = analyze_dependencies_pure(nodes)
    
    return WorkflowBuildOutput(
        nodes=nodes,
        edges=edges,
        errors=errors,
        warnings=warnings
    )


@dataclass(frozen=True)
class StepParsingResult:
    """Result of parsing JSON steps"""
    steps: List[Step]
    errors: List[str]
    warnings: List[str]


def parse_json_steps_pure(
    json_steps: List[Dict[str, Any]], 
    context: StepContext
) -> StepParsingResult:
    """
    Parse JSON steps to Step objects (pure function)
    """
    steps = []
    errors = []
    warnings = []
    
    for i, json_step in enumerate(json_steps):
        try:
            step_type_str = json_step.get("type", "")
            cmd = json_step.get("cmd", [])
            
            if not step_type_str:
                errors.append(f"Step {i}: missing 'type' field")
                continue
            
            # Convert string to StepType
            try:
                step_type = StepType(step_type_str)
            except ValueError:
                errors.append(f"Step {i}: invalid type '{step_type_str}'")
                continue
            
            # Create Step object
            step = Step(
                type=step_type,
                cmd=cmd,
                allow_failure=json_step.get("allow_failure", False),
                show_output=json_step.get("show_output", False),
                cwd=json_step.get("cwd"),
                force_env_type=json_step.get("force_env_type")
            )
            steps.append(step)
            
        except Exception as e:
            errors.append(f"Step {i}: {str(e)}")
    
    return StepParsingResult(steps=steps, errors=errors, warnings=warnings)


def resolve_dependencies_pure(
    steps: List[Step], 
    context: StepContext
) -> List[Step]:
    """
    Resolve dependencies and add necessary preparation steps (pure function)
    """
    resolved = []
    required_dirs = set()
    
    for step in steps:
        # Check if step requires directories
        if step.type in [StepType.COPY, StepType.MOVE, StepType.TOUCH]:
            if step.cmd and len(step.cmd) >= 1:
                target_path = step.cmd[-1] if step.type != StepType.TOUCH else step.cmd[0]
                dir_path = extract_directory_pure(target_path)
                if dir_path and dir_path not in required_dirs:
                    # Add mkdir step
                    mkdir_step = Step(
                        type=StepType.MKDIR,
                        cmd=[dir_path],
                        allow_failure=True
                    )
                    resolved.append(mkdir_step)
                    required_dirs.add(dir_path)
        
        resolved.append(step)
    
    return resolved


def optimize_steps_pure(steps: List[Step]) -> List[Step]:
    """
    Optimize step sequence (pure function)
    """
    if not steps:
        return []
    
    optimized = []
    seen_mkdirs = set()
    
    for step in steps:
        # Remove duplicate mkdir steps
        if step.type == StepType.MKDIR:
            if step.cmd and step.cmd[0] in seen_mkdirs:
                continue  # Skip duplicate
            if step.cmd:
                seen_mkdirs.add(step.cmd[0])
        
        optimized.append(step)
    
    return optimized


def step_to_node_pure(
    step: Step, 
    index: int, 
    context: StepContext
) -> StepProcessingResult:
    """
    Convert a Step to a RequestNode (pure function)
    """
    try:
        # Extract resource information
        resources = extract_step_resources_pure(step)
        
        # Create node ID
        node_id = f"step_{index}"
        
        # Create metadata
        metadata = {
            'step_type': step.type.value,
            'step_cmd': step.cmd,
            'original_index': index
        }
        
        # Note: We don't create the actual request here to keep it pure
        # The request will be created later when needed
        node = RequestNode(
            id=node_id,
            request=None,  # Will be set later
            creates_files=resources.creates_files,
            creates_dirs=resources.creates_dirs,
            reads_files=resources.reads_files,
            requires_dirs=resources.requires_dirs,
            metadata=metadata
        )
        
        return StepProcessingResult(node=node, error=None, warning=None)
        
    except Exception as e:
        return StepProcessingResult(
            node=None,
            error=f"Failed to process step {index}: {str(e)}",
            warning=None
        )


@dataclass(frozen=True)
class StepResources:
    """Resources used/created by a step"""
    creates_files: List[str]
    creates_dirs: List[str]
    reads_files: List[str]
    requires_dirs: List[str]


def extract_step_resources_pure(step: Step) -> StepResources:
    """
    Extract resource information from a step (pure function)
    """
    creates_files = []
    creates_dirs = []
    reads_files = []
    requires_dirs = []
    
    if step.type == StepType.TOUCH and step.cmd:
        creates_files.append(step.cmd[0])
        dir_path = extract_directory_pure(step.cmd[0])
        if dir_path:
            requires_dirs.append(dir_path)
    
    elif step.type == StepType.MKDIR and step.cmd:
        creates_dirs.append(step.cmd[0])
    
    elif step.type == StepType.COPY and len(step.cmd) >= 2:
        reads_files.append(step.cmd[0])
        creates_files.append(step.cmd[1])
        dir_path = extract_directory_pure(step.cmd[1])
        if dir_path:
            requires_dirs.append(dir_path)
    
    elif step.type == StepType.MOVE and len(step.cmd) >= 2:
        reads_files.append(step.cmd[0])
        creates_files.append(step.cmd[1])
        dir_path = extract_directory_pure(step.cmd[1])
        if dir_path:
            requires_dirs.append(dir_path)
    
    return StepResources(
        creates_files=creates_files,
        creates_dirs=creates_dirs,
        reads_files=reads_files,
        requires_dirs=requires_dirs
    )


def extract_directory_pure(file_path: str) -> Optional[str]:
    """
    Extract directory path from a file path (pure function)
    """
    if not file_path or "/" not in file_path:
        return None
    
    parts = file_path.rsplit("/", 1)
    if len(parts) == 2 and parts[0]:
        return parts[0]
    return None


def analyze_dependencies_pure(nodes: List[RequestNode]) -> List[Tuple[str, str]]:
    """
    Analyze dependencies between nodes and create edges (pure function)
    """
    edges = []
    
    # Create resource maps
    file_creators = {}  # file_path -> node_id
    dir_creators = {}   # dir_path -> node_id
    
    # First pass: record what each node creates
    for node in nodes:
        for file_path in node.creates_files:
            file_creators[file_path] = node.id
        for dir_path in node.creates_dirs:
            dir_creators[dir_path] = node.id
    
    # Second pass: find dependencies
    for node in nodes:
        # Check file dependencies
        for file_path in node.reads_files:
            if file_path in file_creators:
                creator_id = file_creators[file_path]
                if creator_id != node.id:  # No self-edges
                    edges.append((creator_id, node.id))
        
        # Check directory dependencies
        for dir_path in node.requires_dirs:
            if dir_path in dir_creators:
                creator_id = dir_creators[dir_path]
                if creator_id != node.id:  # No self-edges
                    edges.append((creator_id, node.id))
    
    # Remove duplicates while preserving order
    seen = set()
    unique_edges = []
    for edge in edges:
        if edge not in seen:
            seen.add(edge)
            unique_edges.append(edge)
    
    return unique_edges