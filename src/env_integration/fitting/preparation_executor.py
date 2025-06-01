"""
Preparation executor for generating pre-workflow tasks
"""
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
import logging

from src.env_integration.fitting.environment_inspector import (
    EnvironmentInspector, ResourceStatus, ResourceType, ResourceRequirement
)
from src.env_integration.fitting.docker_state_manager import DockerStateManager
from src.env_integration.fitting.preparation_error_handler import (
    PreparationErrorHandler, RobustPreparationExecutor, ErrorSeverity, ErrorCategory
)
from src.operations.docker.docker_request import DockerRequest, DockerOpType
from src.operations.file.file_request import FileRequest
from src.operations.file.file_op_type import FileOpType
from src.context.execution_context import ExecutionContext


@dataclass
class PreparationTask:
    """Represents a preparation task that needs to be executed"""
    task_id: str
    task_type: str  # "docker_run", "mkdir", "docker_remove", etc.
    request_object: object  # The actual request object to execute
    dependencies: List[str]  # Task IDs this task depends on
    description: str
    parallel_group: Optional[str] = None  # Group ID for parallel execution


class PreparationExecutor:
    """Generates preparation tasks based on environment inspection results"""
    
    def __init__(self, operations, context: ExecutionContext):
        """Initialize with operations container and execution context
        
        Args:
            operations: Operations container for creating requests
            context: Execution context with configuration and Docker names
        """
        self.operations = operations
        self.context = context
        self.inspector = EnvironmentInspector(operations)
        self.state_manager = DockerStateManager()
        self.error_handler = PreparationErrorHandler()
        self.logger = logging.getLogger(__name__)
        self._task_counter = 0
    
    def analyze_and_prepare(self, workflow_tasks: List) -> Tuple[List[PreparationTask], Dict[str, ResourceStatus]]:
        """Analyze workflow tasks and generate preparation tasks
        
        Args:
            workflow_tasks: List of workflow task objects
            
        Returns:
            Tuple of (preparation_tasks, resource_status_map)
        """
        try:
            # Pre-execution validation
            validation_errors = self._validate_environment()
            if validation_errors:
                self.logger.warning(f"Environment validation found {len(validation_errors)} issues")
                for error in validation_errors:
                    self.logger.warning(f"Validation: {error}")
            
            # Extract requirements from workflow
            requirements = self.inspector.extract_requirements_from_workflow_tasks(workflow_tasks)
            
            # Group requirements by type
            container_requirements = [r for r in requirements if r.resource_type == ResourceType.DOCKER_CONTAINER]
            directory_requirements = [r for r in requirements if r.resource_type == ResourceType.DIRECTORY]
            image_requirements = [r for r in requirements if r.resource_type == ResourceType.DOCKER_IMAGE]
            
            # Inspect current environment state
            container_statuses = {}
            directory_statuses = {}
            image_statuses = {}
            
            if container_requirements:
                container_names = [r.identifier for r in container_requirements]
                container_statuses = self.inspector.inspect_docker_containers(container_names)
            
            if directory_requirements:
                directory_paths = [r.identifier for r in directory_requirements]
                directory_statuses = self.inspector.inspect_directories(directory_paths)
            
            if image_requirements:
                image_names = [r.identifier for r in image_requirements]
                image_statuses = self.inspector.inspect_docker_images(image_names)
            
            # Combine all statuses
            all_statuses = {**container_statuses, **directory_statuses, **image_statuses}
            
            # Generate preparation tasks
            preparation_tasks = self._generate_preparation_tasks(all_statuses)
            
            return preparation_tasks, all_statuses
            
        except Exception as e:
            context = {
                "workflow_tasks_count": len(workflow_tasks),
                "operation": "analyze_and_prepare"
            }
            prep_error = self.error_handler.handle_error(e, context)
            self.logger.error(f"Preparation analysis failed: {prep_error.message}")
            # Return empty results on failure
            return [], {}
    
    def _generate_preparation_tasks(self, statuses: Dict[str, ResourceStatus]) -> List[PreparationTask]:
        """Generate preparation tasks based on resource statuses
        
        Args:
            statuses: Dict mapping resource identifier to ResourceStatus
            
        Returns:
            List of PreparationTask objects
        """
        tasks = []
        
        # Track tasks that can run in parallel
        parallel_docker_tasks = []
        parallel_mkdir_tasks = []
        parallel_image_tasks = []
        
        for identifier, status in statuses.items():
            if not status.needs_preparation:
                continue
            
            if status.resource_type == ResourceType.DOCKER_CONTAINER:
                container_tasks = self._create_container_preparation_tasks(identifier, status)
                parallel_docker_tasks.extend(container_tasks)
                
            elif status.resource_type == ResourceType.DIRECTORY:
                mkdir_task = self._create_mkdir_preparation_task(identifier, status)
                if mkdir_task:
                    parallel_mkdir_tasks.append(mkdir_task)
            
            elif status.resource_type == ResourceType.DOCKER_IMAGE:
                image_task = self._create_image_preparation_task(identifier, status)
                if image_task:
                    parallel_image_tasks.append(image_task)
        
        # Assign parallel groups
        # Docker tasks and mkdir tasks can run in parallel with each other
        for task in parallel_docker_tasks:
            task.parallel_group = "docker_preparation"
            tasks.append(task)
        
        for task in parallel_mkdir_tasks:
            task.parallel_group = "mkdir_preparation"
            tasks.append(task)
        
        for task in parallel_image_tasks:
            task.parallel_group = "image_preparation"
            tasks.append(task)
        
        return tasks
    
    def _create_container_preparation_tasks(self, container_name: str, status: ResourceStatus) -> List[PreparationTask]:
        """Create preparation tasks for Docker container
        
        Args:
            container_name: Name of the container
            status: Current status of the container
            
        Returns:
            List of PreparationTask objects
        """
        tasks = []
        
        if "remove_stopped_container" in status.preparation_actions:
            # Remove stopped container first
            remove_task = self._create_docker_remove_task(container_name)
            tasks.append(remove_task)
        
        if "run_new_container" in status.preparation_actions:
            # Run new container (now returns multiple tasks for build/remove/run)
            run_tasks = self._create_docker_run_task(container_name)
            
            # If we're removing first, first run task depends on remove
            if tasks and run_tasks:
                run_tasks[0].dependencies.append(tasks[-1].task_id)
            
            tasks.extend(run_tasks)
        
        return tasks
    
    def _create_mkdir_preparation_task(self, directory_path: str, status: ResourceStatus) -> Optional[PreparationTask]:
        """Create mkdir preparation task
        
        Args:
            directory_path: Path to the directory
            status: Current status of the directory
            
        Returns:
            PreparationTask object or None
        """
        if "create_directory" not in status.preparation_actions:
            return None
        
        task_id = self._next_task_id("mkdir")
        
        # Create mkdir request
        mkdir_request = FileRequest(
            op=FileOpType.MKDIR,
            path=directory_path
        )
        
        return PreparationTask(
            task_id=task_id,
            task_type="mkdir",
            request_object=mkdir_request,
            dependencies=[],
            description=f"Create directory: {directory_path}"
        )
    
    def _create_image_preparation_task(self, image_name: str, status: ResourceStatus) -> Optional[PreparationTask]:
        """Create image preparation task
        
        Args:
            image_name: Name of the Docker image
            status: Current status of the image
            
        Returns:
            PreparationTask object or None
        """
        if "build_or_pull_image" not in status.preparation_actions:
            return None
        
        task_id = self._next_task_id("image_prepare")
        
        # Try to pull the image first (for public images)
        # Note: This could be enhanced to check if it's a custom image that needs building
        try:
            # Check if this is a standard image (contains no slashes or only one slash for registry/image)
            is_standard_image = image_name.count('/') <= 1 and not any(char in image_name for char in [':', '@']) or ':' in image_name
            
            if is_standard_image:
                # Try to pull standard images like python:3.10, ubuntu:latest, etc.
                from src.operations.shell.shell_request import ShellRequest
                pull_request = ShellRequest([
                    "docker", "pull", image_name
                ])
                
                return PreparationTask(
                    task_id=task_id,
                    task_type="image_pull",
                    request_object=pull_request,
                    dependencies=[],
                    description=f"Pull Docker image: {image_name}"
                )
            else:
                # For custom images, we would need to build them
                # This requires more context about where the Dockerfile is
                # For now, skip custom image building
                return None
                
        except Exception:
            # If pull strategy fails, skip image preparation
            # The system will handle missing images during execution
            return None
    
    def _create_docker_remove_task(self, container_name: str) -> PreparationTask:
        """Create Docker container removal task with force option"""
        task_id = self._next_task_id("docker_remove")
        
        # Use force remove to handle running containers
        remove_request = DockerRequest(
            op=DockerOpType.REMOVE,
            container=container_name,
            options={"f": ""}  # Force remove flag
        )
        
        return PreparationTask(
            task_id=task_id,
            task_type="docker_remove",
            request_object=remove_request,
            dependencies=[],
            description=f"Remove stopped container: {container_name}"
        )
    
    def _create_docker_run_task(self, container_name: str) -> List[PreparationTask]:
        """Create Docker container run task (with rebuild/recreate logic)"""
        tasks = []
        
        # Check if rebuilds/recreates are needed
        (image_rebuild_needed, oj_image_rebuild_needed, 
         container_recreate_needed, oj_container_recreate_needed) = (
            self.state_manager.check_rebuild_needed(self.context)
        )
        
        # Get Docker names from context
        docker_names = self.context.get_docker_names()
        
        # Determine which image to use based on container name
        is_oj_container = container_name.startswith("cph_ojtools")
        if is_oj_container:
            image_name = docker_names["oj_image_name"]
            needs_image_rebuild = oj_image_rebuild_needed
            needs_container_recreate = oj_container_recreate_needed
        else:
            image_name = docker_names["image_name"]
            needs_image_rebuild = image_rebuild_needed
            needs_container_recreate = container_recreate_needed
        
        # Additional compatibility check for existing containers
        if not needs_container_recreate:
            compatible = self.state_manager.inspect_container_compatibility(
                self.operations, container_name, image_name
            )
            if not compatible:
                needs_container_recreate = True
        
        # Create image build task if needed
        build_task_id = None
        if needs_image_rebuild:
            build_task_id = self._next_task_id("docker_build")
            # Get Dockerfile content through resolver (this triggers the lazy loading)
            dockerfile_content = None
            if is_oj_container:
                dockerfile_content = self.context.oj_dockerfile
            else:
                dockerfile_content = self.context.dockerfile
            
            if dockerfile_content:
                build_request = DockerRequest(
                    op=DockerOpType.BUILD,
                    image=image_name,
                    dockerfile_text=dockerfile_content,
                    options={"t": image_name}
                )
                
                build_task = PreparationTask(
                    task_id=build_task_id,
                    task_type="docker_build",
                    request_object=build_request,
                    dependencies=[],
                    description=f"Build image: {image_name}",
                    parallel_group="docker_preparation"
                )
                tasks.append(build_task)
        
        # Create container remove task if recreation needed
        rebuild_remove_task_id = None
        if needs_container_recreate:
            # Check if container exists first
            ps_result = self.operations.resolve("docker_driver").ps(
                all=True, show_output=False, names_only=True
            )
            if container_name in ps_result:
                rebuild_remove_task_id = self._next_task_id("docker_remove")
                remove_request = DockerRequest(
                    op=DockerOpType.REMOVE,
                    container=container_name,
                    options={"f": ""}  # Force remove flag
                )
                
                remove_task = PreparationTask(
                    task_id=rebuild_remove_task_id,
                    task_type="docker_remove",
                    request_object=remove_request,
                    dependencies=[],
                    description=f"Remove old container: {container_name}",
                    parallel_group="docker_preparation"
                )
                tasks.append(remove_task)
        
        # Create container run task
        run_task_id = self._next_task_id("docker_run")
        run_dependencies = []
        
        # Add dependencies based on what needs to be done first
        if needs_image_rebuild and build_task_id:
            run_dependencies.append(build_task_id)
        if needs_container_recreate and rebuild_remove_task_id:
            run_dependencies.append(rebuild_remove_task_id)
        
        # Add volume mount options to make project files accessible in container
        import os
        project_path = os.getcwd()
        volume_options = {
            "v": f"{project_path}:/workspace"
        }
        
        run_request = DockerRequest(
            op=DockerOpType.RUN,
            image=image_name,
            container=container_name,
            command="tail -f /dev/null",  # Keep container running
            options=volume_options
        )
        
        run_task = PreparationTask(
            task_id=run_task_id,
            task_type="docker_run",
            request_object=run_request,
            dependencies=run_dependencies,
            description=f"Run container: {container_name} from image: {image_name}",
            parallel_group="docker_preparation"
        )
        tasks.append(run_task)
        
        # Update state after successful preparation
        self.state_manager.update_state(self.context)
        
        return tasks
    
    def _next_task_id(self, prefix: str) -> str:
        """Generate next task ID"""
        self._task_counter += 1
        return f"{prefix}_{self._task_counter:03d}"
    
    def convert_to_workflow_requests(self, preparation_tasks: List[PreparationTask]) -> List:
        """Convert preparation tasks to workflow-compatible request objects
        
        Args:
            preparation_tasks: List of PreparationTask objects
            
        Returns:
            List of request objects ready for workflow execution
        """
        # Sort tasks by dependencies and parallel groups
        sorted_tasks = self._sort_tasks_by_dependencies(preparation_tasks)
        
        # Extract request objects
        return [task.request_object for task in sorted_tasks]
    
    def _sort_tasks_by_dependencies(self, tasks: List[PreparationTask]) -> List[PreparationTask]:
        """Sort tasks by dependencies using topological sort
        
        Args:
            tasks: List of PreparationTask objects
            
        Returns:
            List of sorted PreparationTask objects
        """
        # Create task lookup
        task_map = {task.task_id: task for task in tasks}
        
        # Simple dependency resolution (could be enhanced with graph algorithms)
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
    
    def _validate_environment(self) -> List[str]:
        """Validate the execution environment for common issues
        
        Returns:
            List of validation error messages
        """
        errors = []
        
        try:
            # Check Docker daemon accessibility
            docker_driver = self.operations.resolve("docker_driver")
            ps_result = docker_driver.ps(show_output=False)
            if not hasattr(ps_result, 'returncode') or ps_result.returncode != 0:
                errors.append("Docker daemon may not be accessible")
        except Exception:
            errors.append("Failed to access Docker driver")
        
        try:
            # Check basic file system access
            import os
            current_dir = os.getcwd()
            if not os.access(current_dir, os.R_OK | os.W_OK):
                errors.append(f"Insufficient permissions for current directory: {current_dir}")
        except Exception:
            errors.append("Failed to validate file system access")
        
        try:
            # Check available disk space (basic check)
            import shutil
            total, used, free = shutil.disk_usage(".")
            if free < 1024 * 1024 * 100:  # Less than 100MB free
                errors.append("Low disk space available")
        except Exception:
            errors.append("Failed to check disk space")
        
        # Validate context configuration
        if not hasattr(self.context, 'env_type') or not self.context.env_type:
            errors.append("Environment type not specified in context")
        
        if hasattr(self.context, 'env_type') and self.context.env_type == 'docker':
            try:
                docker_names = self.context.get_docker_names()
                if not docker_names.get('image_name'):
                    errors.append("Docker image name not configured")
                if not docker_names.get('container_name'):
                    errors.append("Docker container name not configured")
            except Exception:
                errors.append("Failed to get Docker configuration from context")
        
        return errors
    
    def execute_preparation_with_retry(self, preparation_tasks: List[PreparationTask]) -> Tuple[bool, List[str]]:
        """Execute preparation tasks with robust error handling
        
        Args:
            preparation_tasks: List of preparation tasks to execute
            
        Returns:
            Tuple of (success, error_messages)
        """
        if not preparation_tasks:
            return True, []
        
        robust_executor = RobustPreparationExecutor(self, self.error_handler)
        success, successful_tasks, failed_tasks = robust_executor.execute_with_retry(preparation_tasks)
        
        error_messages = []
        if failed_tasks:
            for task in failed_tasks:
                error_messages.append(f"Task {task.task_id} ({task.description}) failed")
        
        # Generate error report
        error_report = self.error_handler.generate_error_report()
        if error_report.get("status") == "errors_found":
            self.logger.warning(f"Preparation completed with {len(failed_tasks)} failures")
            self.logger.info(f"Error report: {error_report}")
        
        return success, error_messages