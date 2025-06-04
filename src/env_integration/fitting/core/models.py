"""
Core models and data structures for environment fitting
"""
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum


class ResourceType(Enum):
    """Resource types that can be inspected"""
    DOCKER_CONTAINER = "docker_container"
    DOCKER_IMAGE = "docker_image"
    KUBERNETES_POD = "kubernetes_pod"
    KUBERNETES_SERVICE = "kubernetes_service"
    KUBERNETES_DEPLOYMENT = "kubernetes_deployment"
    DIRECTORY = "directory"
    FILE = "file"
    NETWORK = "network"


@dataclass
class ResourceRequirement:
    """Represents a resource requirement for workflow execution"""
    resource_type: ResourceType
    identifier: str  # container name, image name, file path, etc.
    required_state: str  # "running", "exists", "available", etc.
    context_info: Optional[Dict] = None


@dataclass
class ContainerRequirement(ResourceRequirement):
    """Specific requirement for container resources"""
    image_name: Optional[str] = None
    restart_policy: Optional[str] = None
    environment_vars: Optional[Dict[str, str]] = None
    volume_mounts: Optional[List[Dict[str, str]]] = None
    
    def __post_init__(self):
        if self.resource_type not in [ResourceType.DOCKER_CONTAINER, ResourceType.KUBERNETES_POD]:
            raise ValueError(f"ContainerRequirement requires container resource type, got {self.resource_type}")


@dataclass 
class NetworkRequirement(ResourceRequirement):
    """Specific requirement for network resources"""
    ports: Optional[List[int]] = None
    protocol: Optional[str] = None
    external_access: bool = False
    
    def __post_init__(self):
        if self.resource_type != ResourceType.NETWORK:
            raise ValueError(f"NetworkRequirement requires network resource type, got {self.resource_type}")


@dataclass
class ResourceStatus:
    """Current status of a resource"""
    resource_type: ResourceType
    identifier: str
    current_state: str  # "running", "stopped", "missing", etc.
    exists: bool
    needs_preparation: bool
    preparation_actions: List[str]  # Actions needed to reach required state
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class PreparationTask:
    """Represents a preparation task that needs to be executed"""
    task_id: str
    task_type: str  # "docker_run", "mkdir", "docker_remove", etc.
    request_object: object  # The actual request object to execute
    dependencies: List[str]  # Task IDs this task depends on
    description: str
    parallel_group: Optional[str] = None  # Group ID for parallel execution
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class RebuildDecision:
    """Decision about what needs to be rebuilt or recreated"""
    image_rebuild_needed: bool = False
    oj_image_rebuild_needed: bool = False
    container_recreate_needed: bool = False
    oj_container_recreate_needed: bool = False
    reason: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    
    def any_action_needed(self) -> bool:
        """Check if any rebuild/recreate action is needed"""
        return any([
            self.image_rebuild_needed,
            self.oj_image_rebuild_needed,
            self.container_recreate_needed,
            self.oj_container_recreate_needed
        ])


@dataclass
class PreparationResult:
    """Result of preparation execution"""
    success: bool
    preparation_tasks: List[PreparationTask]
    successful_tasks: List[PreparationTask]
    failed_tasks: List[PreparationTask]
    error_messages: List[str]
    resource_statuses: Dict[str, ResourceStatus]
    execution_time_seconds: Optional[float] = None
    
    def get_summary(self) -> Dict[str, Any]:
        """Get a summary of preparation results"""
        return {
            "success": self.success,
            "total_tasks": len(self.preparation_tasks),
            "successful_tasks": len(self.successful_tasks),
            "failed_tasks": len(self.failed_tasks),
            "error_count": len(self.error_messages),
            "execution_time": self.execution_time_seconds
        }


class ErrorSeverity(Enum):
    """Error severity levels for preparation failures"""
    CRITICAL = "critical"      # Prevents any execution
    HIGH = "high"             # Prevents current operation but alternatives may exist
    MEDIUM = "medium"         # May affect performance or functionality
    LOW = "low"              # Minor issues that don't block execution


class ErrorCategory(Enum):
    """Categories of preparation errors"""
    DOCKER_DAEMON = "docker_daemon"
    DOCKER_IMAGE = "docker_image"
    DOCKER_CONTAINER = "docker_container"
    KUBERNETES_API = "kubernetes_api"
    KUBERNETES_RESOURCE = "kubernetes_resource"
    FILESYSTEM = "filesystem"
    NETWORK = "network"
    RESOURCE = "resource"
    CONFIGURATION = "configuration"
    DEPENDENCY = "dependency"


@dataclass
class PreparationError:
    """Represents a preparation error with context"""
    category: ErrorCategory
    severity: ErrorSeverity
    message: str
    details: Dict[str, Any]
    retry_possible: bool = False
    suggested_action: Optional[str] = None
    context: Optional[Dict[str, Any]] = None