"""
Pure data structures for execution context
"""
from dataclasses import dataclass, field
from typing import Dict, Optional, List, Any


@dataclass(frozen=True)
class ExecutionData:
    """Immutable execution data"""
    command_type: str
    language: str
    contest_name: str
    problem_name: str
    env_type: str
    env_json: Dict[str, Any] = field(default_factory=dict)
    
    # Optional fields
    working_directory: Optional[str] = None
    contest_current_path: Optional[str] = None
    contest_stock_path: Optional[str] = None
    contest_template_path: Optional[str] = None
    contest_temp_path: Optional[str] = None
    workspace_path: Optional[str] = None
    source_file_name: Optional[str] = None
    language_id: Optional[str] = None
    task_label: Optional[str] = None


@dataclass(frozen=True)
class DockerNames:
    """Immutable Docker naming data"""
    image_name: str
    container_name: str
    oj_image_name: str
    oj_container_name: str


def create_docker_names_pure(
    contest_name: str,
    problem_name: str,
    language: str,
    env_type: str
) -> DockerNames:
    """
    Create Docker names from context data (pure function)
    """
    # Generate consistent names
    base_name = f"cph_{contest_name}_{problem_name}_{language}"
    
    return DockerNames(
        image_name=f"{base_name}_image",
        container_name=f"{base_name}_container",
        oj_image_name=f"{base_name}_oj_image",
        oj_container_name=f"{base_name}_oj_container"
    )


def validate_execution_data_pure(data: ExecutionData) -> List[str]:
    """
    Validate execution data and return list of errors (pure function)
    """
    errors = []
    
    # Required fields
    if not data.command_type:
        errors.append("command_type is required")
    if not data.language:
        errors.append("language is required")
    if not data.contest_name:
        errors.append("contest_name is required")
    if not data.problem_name:
        errors.append("problem_name is required")
    if not data.env_type:
        errors.append("env_type is required")
    
    # Validate env_type
    if data.env_type not in ["local", "docker"]:
        errors.append(f"env_type must be 'local' or 'docker', got '{data.env_type}'")
    
    # Validate language exists in env_json
    if data.env_json and data.language not in data.env_json:
        errors.append(f"language '{data.language}' not found in env_json")
    
    # Validate command exists
    if data.env_json and data.language in data.env_json:
        commands = data.env_json[data.language].get("commands", {})
        if data.command_type not in commands:
            errors.append(f"command_type '{data.command_type}' not found for language '{data.language}'")
    
    return errors


def create_format_dict_pure(data: ExecutionData) -> Dict[str, str]:
    """
    Create formatting dictionary from execution data (pure function)
    """
    format_dict = {
        "command_type": data.command_type,
        "language": data.language,
        "contest_name": data.contest_name,
        "problem_name": data.problem_name,
        "env_type": data.env_type,
        "task_label": data.task_label or data.problem_name,
    }
    
    # Add optional fields if present
    if data.working_directory:
        format_dict["working_directory"] = data.working_directory
    if data.contest_current_path:
        format_dict["contest_current_path"] = data.contest_current_path
    if data.contest_stock_path:
        format_dict["contest_stock_path"] = data.contest_stock_path
    if data.contest_template_path:
        format_dict["contest_template_path"] = data.contest_template_path
    if data.contest_temp_path:
        format_dict["contest_temp_path"] = data.contest_temp_path
    if data.workspace_path:
        format_dict["workspace_path"] = data.workspace_path
    if data.source_file_name:
        format_dict["source_file_name"] = data.source_file_name
    if data.language_id:
        format_dict["language_id"] = data.language_id
    
    # Add Docker names if Docker environment
    if data.env_type == "docker":
        docker_names = create_docker_names_pure(
            data.contest_name,
            data.problem_name,
            data.language,
            data.env_type
        )
        format_dict.update({
            "image_name": docker_names.image_name,
            "container_name": docker_names.container_name,
            "oj_image_name": docker_names.oj_image_name,
            "oj_container_name": docker_names.oj_container_name
        })
    
    return format_dict


def format_string_pure(template: str, format_dict: Dict[str, str]) -> str:
    """
    Format a string template with the given dictionary (pure function)
    
    Returns the formatted string. Missing keys are left as-is.
    """
    try:
        return template.format(**format_dict)
    except KeyError:
        # Format with available keys only
        result = template
        for key, value in format_dict.items():
            result = result.replace(f"{{{key}}}", str(value))
        return result


def resolve_config_path_pure(
    path: List[str],
    env_json: Dict[str, Any],
    language: str,
    command_type: str
) -> Optional[Any]:
    """
    Resolve a configuration path in env_json (pure function)
    
    Args:
        path: Path segments to resolve
        env_json: The environment configuration
        language: Current language
        command_type: Current command type
        
    Returns:
        The resolved value or None if not found
    """
    if not env_json or not path:
        return None
    
    # Start from language config
    current = env_json.get(language, {})
    
    # Navigate through path
    for segment in path:
        if isinstance(current, dict):
            current = current.get(segment)
        else:
            return None
    
    return current


@dataclass(frozen=True)
class StepContextData:
    """Pure data for step context"""
    contest_name: str
    problem_name: str
    language: str
    env_type: str
    command_type: str
    workspace_path: str
    contest_current_path: str
    contest_stock_path: Optional[str] = None
    contest_template_path: Optional[str] = None
    contest_temp_path: Optional[str] = None
    source_file_name: Optional[str] = None
    language_id: Optional[str] = None


def execution_data_to_step_context_pure(data: ExecutionData) -> StepContextData:
    """
    Convert ExecutionData to StepContextData (pure function)
    """
    return StepContextData(
        contest_name=data.contest_name,
        problem_name=data.problem_name or "",
        language=data.language,
        env_type=data.env_type,
        command_type=data.command_type,
        workspace_path=data.workspace_path or "./workspace",
        contest_current_path=data.contest_current_path or "./contest_current",
        contest_stock_path=data.contest_stock_path,
        contest_template_path=data.contest_template_path,
        contest_temp_path=data.contest_temp_path,
        source_file_name=data.source_file_name,
        language_id=data.language_id
    )