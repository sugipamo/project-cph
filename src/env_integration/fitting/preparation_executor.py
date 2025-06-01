"""
Preparation executor for generating pre-workflow tasks
"""
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass

from src.env_integration.fitting.environment_inspector import (
    EnvironmentInspector, ResourceStatus, ResourceType, ResourceRequirement
)
from src.env_integration.fitting.docker_state_manager import DockerStateManager
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
        self._task_counter = 0
    
    def analyze_and_prepare(self, workflow_tasks: List) -> Tuple[List[PreparationTask], Dict[str, ResourceStatus]]:
        """Analyze workflow tasks and generate preparation tasks
        
        Args:
            workflow_tasks: List of workflow task objects
            
        Returns:
            Tuple of (preparation_tasks, resource_status_map)
        """
        # Extract requirements from workflow
        requirements = self.inspector.extract_requirements_from_workflow_tasks(workflow_tasks)
        
        # Group requirements by type
        container_requirements = [r for r in requirements if r.resource_type == ResourceType.DOCKER_CONTAINER]
        directory_requirements = [r for r in requirements if r.resource_type == ResourceType.DIRECTORY]
        
        # Inspect current environment state
        container_statuses = {}
        directory_statuses = {}
        
        if container_requirements:
            container_names = [r.identifier for r in container_requirements]
            container_statuses = self.inspector.inspect_docker_containers(container_names)
        
        if directory_requirements:
            directory_paths = [r.identifier for r in directory_requirements]
            directory_statuses = self.inspector.inspect_directories(directory_paths)
        
        # Combine all statuses
        all_statuses = {**container_statuses, **directory_statuses}
        
        # Generate preparation tasks
        preparation_tasks = self._generate_preparation_tasks(all_statuses)
        
        return preparation_tasks, all_statuses
    
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
        
        # Assign parallel groups
        # Docker tasks and mkdir tasks can run in parallel with each other
        for task in parallel_docker_tasks:
            task.parallel_group = "docker_preparation"
            tasks.append(task)
        
        for task in parallel_mkdir_tasks:
            task.parallel_group = "mkdir_preparation"
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
    
    def _create_docker_remove_task(self, container_name: str) -> PreparationTask:
        """Create Docker container removal task"""
        task_id = self._next_task_id("docker_remove")
        
        remove_request = DockerRequest(
            op=DockerOpType.REMOVE,
            container=container_name
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
                    container=container_name
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
        
        run_request = DockerRequest(
            op=DockerOpType.RUN,
            image=image_name,
            container=container_name,
            command="tail -f /dev/null"  # Keep container running
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