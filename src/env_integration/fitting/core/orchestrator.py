"""
Preparation orchestrator for unified environment preparation control
"""
import time
import logging
from typing import List, Dict, Optional, Tuple

from .interfaces import ProviderSet
from .models import (
    PreparationResult, PreparationTask, ResourceStatus,
    ResourceRequirement, ResourceType
)
from ..registry import ProviderRegistry, get_global_registry


class PreparationOrchestrator:
    """Orchestrates environment preparation using pluggable providers"""
    
    def __init__(self, registry: Optional[ProviderRegistry] = None):
        """Initialize orchestrator with provider registry
        
        Args:
            registry: Provider registry (uses global registry if None)
        """
        self.registry = registry or get_global_registry()
        self.logger = logging.getLogger(__name__)
    
    def prepare_environment(self, context, workflow_tasks: List, operations) -> PreparationResult:
        """Prepare environment for workflow execution
        
        Args:
            context: Execution context with environment configuration
            workflow_tasks: List of workflow task objects
            operations: Operations container
            
        Returns:
            PreparationResult with execution details
        """
        start_time = time.time()
        
        try:
            # Get provider set for the environment type
            env_type = getattr(context, 'env_type', 'docker')  # Default to docker
            provider_set = self.registry.get_provider_set(env_type, operations, context)
            
            self.logger.info(f"Starting environment preparation for type: {env_type}")
            
            # Phase 1: Extract requirements from workflow
            requirements = provider_set.inspector.extract_requirements_from_workflow_tasks(workflow_tasks)
            self.logger.debug(f"Extracted {len(requirements)} resource requirements")
            
            # Phase 2: Inspect current environment state
            resource_statuses = self._inspect_all_resources(provider_set, requirements)
            self.logger.debug(f"Inspected {len(resource_statuses)} resources")
            
            # Phase 3: Generate preparation tasks
            preparation_tasks = provider_set.generator.generate_preparation_tasks(resource_statuses)
            self.logger.info(f"Generated {len(preparation_tasks)} preparation tasks")
            
            # Phase 4: Execute preparation tasks
            successful_tasks, failed_tasks, error_messages = self._execute_preparation_tasks(
                preparation_tasks, provider_set, operations
            )
            
            execution_time = time.time() - start_time
            success = len(failed_tasks) == 0
            
            self.logger.info(
                f"Environment preparation completed: success={success}, "
                f"tasks={len(preparation_tasks)}, failures={len(failed_tasks)}, "
                f"time={execution_time:.2f}s"
            )
            
            return PreparationResult(
                success=success,
                preparation_tasks=preparation_tasks,
                successful_tasks=successful_tasks,
                failed_tasks=failed_tasks,
                error_messages=error_messages,
                resource_statuses=resource_statuses,
                execution_time_seconds=execution_time
            )
            
        except Exception as e:
            execution_time = time.time() - start_time
            error_message = f"Environment preparation failed: {str(e)}"
            self.logger.error(error_message)
            
            return PreparationResult(
                success=False,
                preparation_tasks=[],
                successful_tasks=[],
                failed_tasks=[],
                error_messages=[error_message],
                resource_statuses={},
                execution_time_seconds=execution_time
            )
    
    def _inspect_all_resources(self, provider_set: ProviderSet, requirements: List[ResourceRequirement]) -> Dict[str, ResourceStatus]:
        """Inspect all resources based on requirements
        
        Args:
            provider_set: Provider set for the environment
            requirements: List of resource requirements
            
        Returns:
            Dict mapping resource identifier to ResourceStatus
        """
        all_statuses = {}
        
        # Group requirements by type
        container_requirements = [r for r in requirements if r.resource_type in [
            ResourceType.DOCKER_CONTAINER, ResourceType.KUBERNETES_POD
        ]]
        directory_requirements = [r for r in requirements if r.resource_type == ResourceType.DIRECTORY]
        image_requirements = [r for r in requirements if r.resource_type in [
            ResourceType.DOCKER_IMAGE
        ]]
        network_requirements = [r for r in requirements if r.resource_type == ResourceType.NETWORK]
        
        # Inspect containers
        if container_requirements:
            try:
                container_statuses = provider_set.inspector.inspect_containers(container_requirements)
                all_statuses.update(container_statuses)
            except Exception as e:
                self.logger.warning(f"Container inspection failed: {e}")
        
        # Inspect directories
        if directory_requirements:
            try:
                directory_paths = [r.identifier for r in directory_requirements]
                directory_statuses = provider_set.inspector.inspect_directories(directory_paths)
                all_statuses.update(directory_statuses)
            except Exception as e:
                self.logger.warning(f"Directory inspection failed: {e}")
        
        # Inspect images
        if image_requirements:
            try:
                image_names = [r.identifier for r in image_requirements]
                image_statuses = provider_set.inspector.inspect_images(image_names)
                all_statuses.update(image_statuses)
            except Exception as e:
                self.logger.warning(f"Image inspection failed: {e}")
        
        # Inspect networks
        if network_requirements:
            try:
                network_statuses = provider_set.inspector.inspect_networks(network_requirements)
                all_statuses.update(network_statuses)
            except Exception as e:
                self.logger.warning(f"Network inspection failed: {e}")
        
        return all_statuses
    
    def _execute_preparation_tasks(self, preparation_tasks: List[PreparationTask], 
                                 provider_set: ProviderSet, operations) -> Tuple[List[PreparationTask], List[PreparationTask], List[str]]:
        """Execute preparation tasks with error handling
        
        Args:
            preparation_tasks: List of tasks to execute
            provider_set: Provider set for error handling
            operations: Operations container
            
        Returns:
            Tuple of (successful_tasks, failed_tasks, error_messages)
        """
        if not preparation_tasks:
            return [], [], []
        
        # Sort tasks by dependencies
        sorted_tasks = self._sort_tasks_by_dependencies(preparation_tasks)
        
        successful_tasks = []
        failed_tasks = []
        error_messages = []
        
        for task in sorted_tasks:
            try:
                # Execute the task
                unified_driver = operations.resolve("unified_driver")
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
                
                error_msg = f"Task {task.task_id} failed with error: {prep_error}"
                error_messages.append(error_msg)
                failed_tasks.append(task)
                self.logger.error(error_msg)
        
        return successful_tasks, failed_tasks, error_messages
    
    def _sort_tasks_by_dependencies(self, tasks: List[PreparationTask]) -> List[PreparationTask]:
        """Sort tasks by dependencies using topological sort
        
        Args:
            tasks: List of PreparationTask objects
            
        Returns:
            List of sorted PreparationTask objects
        """
        # Create task lookup
        task_map = {task.task_id: task for task in tasks}
        
        # Simple dependency resolution
        sorted_tasks = []
        remaining_tasks = tasks.copy()
        
        while remaining_tasks:
            # Find tasks with no unresolved dependencies
            ready_tasks = []
            for task in remaining_tasks:
                deps_satisfied = all(
                    dep_id in [t.task_id for t in sorted_tasks] 
                    for dep_id in task.dependencies
                )
                if deps_satisfied:
                    ready_tasks.append(task)
            
            if not ready_tasks:
                # Circular dependency or error - add remaining tasks
                self.logger.warning("Possible circular dependency detected, adding remaining tasks")
                sorted_tasks.extend(remaining_tasks)
                break
            
            # Group parallel tasks together
            parallel_groups = {}
            non_parallel_tasks = []
            
            for task in ready_tasks:
                if task.parallel_group:
                    if task.parallel_group not in parallel_groups:
                        parallel_groups[task.parallel_group] = []
                    parallel_groups[task.parallel_group].append(task)
                else:
                    non_parallel_tasks.append(task)
            
            # Add parallel groups first, then non-parallel tasks
            for group_tasks in parallel_groups.values():
                sorted_tasks.extend(group_tasks)
            sorted_tasks.extend(non_parallel_tasks)
            
            # Remove processed tasks
            for task in ready_tasks:
                remaining_tasks.remove(task)
        
        return sorted_tasks
    
    def analyze_and_prepare(self, context, workflow_tasks: List, operations) -> Tuple[List[PreparationTask], Dict[str, ResourceStatus]]:
        """Legacy compatibility method - analyze workflow and generate preparation tasks
        
        Args:
            context: Execution context
            workflow_tasks: List of workflow task objects
            operations: Operations container
            
        Returns:
            Tuple of (preparation_tasks, resource_status_map)
        """
        result = self.prepare_environment(context, workflow_tasks, operations)
        return result.preparation_tasks, result.resource_statuses