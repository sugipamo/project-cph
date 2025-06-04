"""
Legacy compatibility layer for existing fitting module usage
"""
import logging
from typing import List, Dict, Tuple, Optional

from .core.orchestrator import PreparationOrchestrator
from .core.models import PreparationTask, ResourceStatus
from .registry import get_global_registry, register_provider_factory
from .providers.docker import DockerProviderFactory


class LegacyPreparationExecutor:
    """Legacy compatibility wrapper for PreparationExecutor interface"""
    
    def __init__(self, operations, context):
        """Initialize legacy executor with operations and context
        
        Args:
            operations: Operations container
            context: Execution context
        """
        self.operations = operations
        self.context = context
        self.logger = logging.getLogger(__name__)
        
        # Ensure Docker provider is registered
        self._ensure_docker_provider_registered()
        
        # Create orchestrator
        self.orchestrator = PreparationOrchestrator()
    
    def _ensure_docker_provider_registered(self):
        """Ensure Docker provider factory is registered"""
        registry = get_global_registry()
        if not registry.is_env_type_supported("docker"):
            docker_factory = DockerProviderFactory()
            register_provider_factory("docker", docker_factory)
            self.logger.debug("Registered Docker provider factory")
    
    def analyze_and_prepare(self, workflow_tasks: List) -> Tuple[List[PreparationTask], Dict[str, ResourceStatus]]:
        """Legacy interface: Analyze workflow tasks and generate preparation tasks
        
        Args:
            workflow_tasks: List of workflow task objects
            
        Returns:
            Tuple of (preparation_tasks, resource_status_map)
        """
        try:
            result = self.orchestrator.prepare_environment(
                self.context, workflow_tasks, self.operations
            )
            
            return result.preparation_tasks, result.resource_statuses
            
        except Exception as e:
            self.logger.error(f"Legacy preparation analysis failed: {e}")
            return [], {}
    
    def convert_to_workflow_requests(self, preparation_tasks: List[PreparationTask]) -> List:
        """Convert preparation tasks to workflow-compatible request objects
        
        Args:
            preparation_tasks: List of PreparationTask objects
            
        Returns:
            List of request objects ready for workflow execution
        """
        try:
            # Get the appropriate provider set
            env_type = getattr(self.context, 'env_type', 'docker')
            provider_set = get_global_registry().get_provider_set(
                env_type, self.operations, self.context
            )
            
            return provider_set.generator.convert_to_workflow_requests(preparation_tasks)
            
        except Exception as e:
            self.logger.error(f"Legacy task conversion failed: {e}")
            return [task.request_object for task in preparation_tasks]
    
    def execute_preparation_with_retry(self, preparation_tasks: List[PreparationTask]) -> Tuple[bool, List[str]]:
        """Execute preparation tasks with robust error handling
        
        Args:
            preparation_tasks: List of PreparationTask objects
            
        Returns:
            Tuple of (success, error_messages)
        """
        if not preparation_tasks:
            return True, []
        
        try:
            # Get the appropriate provider set for error handling
            env_type = getattr(self.context, 'env_type', 'docker')
            provider_set = get_global_registry().get_provider_set(
                env_type, self.operations, self.context
            )
            
            successful_tasks = []
            failed_tasks = []
            error_messages = []
            
            for task in preparation_tasks:
                try:
                    # Execute the task
                    unified_driver = self.operations.resolve("unified_driver")
                    result = task.request_object.execute(unified_driver)
                    
                    if hasattr(result, 'success') and result.success:
                        successful_tasks.append(task)
                        self.logger.debug(f"Task {task.task_id} succeeded: {task.description}")
                    else:
                        error_msg = f"Task {task.task_id} failed: {getattr(result, 'stderr', 'Unknown error')}"
                        error_messages.append(error_msg)
                        failed_tasks.append(task)
                        self.logger.warning(error_msg)
                        
                except Exception as e:
                    # Use provider's error handler
                    context = {
                        "task_id": task.task_id,
                        "task_type": task.task_type,
                        "description": task.description
                    }
                    prep_error = provider_set.error_handler.handle_error(e, context)
                    
                    error_msg = f"Task {task.task_id} failed with error: {prep_error.message}"
                    error_messages.append(error_msg)
                    failed_tasks.append(task)
                    self.logger.error(error_msg)
            
            success = len(failed_tasks) == 0
            return success, error_messages
            
        except Exception as e:
            error_msg = f"Legacy preparation execution failed: {e}"
            self.logger.error(error_msg)
            return False, [error_msg]


# Backward compatibility alias
PreparationExecutor = LegacyPreparationExecutor


def create_legacy_environment_inspector(operations):
    """Create a legacy EnvironmentInspector instance using the new system
    
    Args:
        operations: Operations container
        
    Returns:
        Docker inspector instance that matches legacy interface
    """
    from .providers.docker.inspector import DockerResourceInspector
    return DockerResourceInspector(operations)


def create_legacy_docker_state_manager(initial_state=None, state_file_path=None):
    """Create a legacy DockerStateManager instance using the new system
    
    Args:
        initial_state: Initial state dict
        state_file_path: Path to state file
        
    Returns:
        Docker state manager instance
    """
    from .providers.docker.state import DockerStateManager
    return DockerStateManager(initial_state, state_file_path)


def create_legacy_preparation_error_handler():
    """Create a legacy PreparationErrorHandler instance using the new system
    
    Returns:
        Docker error handler instance
    """
    from .providers.docker.error_handler import DockerErrorHandler
    return DockerErrorHandler()


# Legacy aliases for backward compatibility
EnvironmentInspector = create_legacy_environment_inspector
DockerStateManager = create_legacy_docker_state_manager  
PreparationErrorHandler = create_legacy_preparation_error_handler