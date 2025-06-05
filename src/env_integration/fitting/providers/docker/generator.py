"""
Docker-specific task generator implementation
"""
import os
import logging
from typing import List, Dict, Optional

from ...core.interfaces import TaskGenerator
from ...core.models import (
    ResourceStatus, PreparationTask, ResourceType
)
from src.operations.docker.docker_request import DockerRequest, DockerOpType
from src.operations.file.file_request import FileRequest
from src.operations.file.file_op_type import FileOpType
from src.operations.shell.shell_request import ShellRequest
from src.pure_functions.docker_path_utils_pure import should_build_custom_docker_image


class DockerTaskGenerator(TaskGenerator):
    """Docker-specific implementation of TaskGenerator"""
    
    def __init__(self, operations, context, state_manager):
        """Initialize Docker task generator
        
        Args:
            operations: Operations container
            context: Execution context (env.json based)
            state_manager: Docker state manager
        """
        self.operations = operations
        self.context = context
        self.state_manager = state_manager
        self.logger = logging.getLogger(__name__)
        self._task_counter = 0
    
    def generate_preparation_tasks(self, statuses: Dict[str, ResourceStatus]) -> List[PreparationTask]:
        """Generate Docker-specific preparation tasks based on resource statuses
        
        Args:
            statuses: Dict mapping resource identifier to ResourceStatus
            
        Returns:
            List of PreparationTask objects
        """
        # Task generators mapping
        task_generators = {
            ResourceType.DOCKER_CONTAINER: self._create_container_preparation_tasks,
            ResourceType.DIRECTORY: self._create_mkdir_preparation_task,
            ResourceType.DOCKER_IMAGE: self._create_image_preparation_task,
        }
        
        # Parallel group assignments
        parallel_group_map = {
            ResourceType.DOCKER_CONTAINER: "docker_preparation",
            ResourceType.DIRECTORY: "mkdir_preparation", 
            ResourceType.DOCKER_IMAGE: "image_preparation",
        }
        
        tasks = []
        
        for identifier, status in statuses.items():
            if not status.needs_preparation:
                continue
            
            # Generate tasks using pure function dispatch
            generator = task_generators.get(status.resource_type)
            if generator:
                generated_tasks = generator(identifier, status)
                if generated_tasks:
                    # Handle both single task and list of tasks
                    if isinstance(generated_tasks, list):
                        for task in generated_tasks:
                            task.parallel_group = parallel_group_map[status.resource_type]
                            tasks.append(task)
                    else:
                        generated_tasks.parallel_group = parallel_group_map[status.resource_type]
                        tasks.append(generated_tasks)
        
        return tasks
    
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
        
        # Check if this is a custom image that needs to be built
        if should_build_custom_docker_image(image_name):
            # Determine which Dockerfile to use
            dockerfile_content = None
            
            if image_name.startswith("ojtools"):
                # OJ-specific image
                dockerfile_content = getattr(self.context, 'oj_dockerfile', None)
                if not dockerfile_content:
                    self.logger.error(f"OJ Dockerfile content not found for image: {image_name}")
                    return None
            else:
                # Language-specific image
                dockerfile_content = getattr(self.context, 'dockerfile', None)
                if not dockerfile_content:
                    self.logger.error(f"Dockerfile content not found for image: {image_name}")
                    return None
            
            build_request = DockerRequest(
                op=DockerOpType.BUILD,
                image=image_name,
                dockerfile_text=dockerfile_content,
                options={"t": image_name}
            )
            
            return PreparationTask(
                task_id=task_id,
                task_type="docker_build",
                request_object=build_request,
                dependencies=[],
                description=f"Build custom Docker image: {image_name}"
            )
        
        # For standard images that can be pulled from registry
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
        # Determine container configuration
        container_config = self._determine_container_config(container_name)
        
        # Generate tasks based on configuration
        tasks = self._generate_docker_tasks(container_config)
        
        # Update state after successful preparation
        self.state_manager.update_state(self.context)
        
        return tasks
    
    def _determine_container_config(self, container_name: str):
        """Determine container configuration based on name and state"""
        # Check if rebuilds/recreates are needed
        rebuild_decision = self.state_manager.check_rebuild_needed(self.context)
        
        # Get Docker names from context
        docker_names = self.context.get_docker_names()
        
        # Determine which image to use based on container name using env.json naming
        is_oj_container = self.context.is_oj_container(container_name)
        if is_oj_container:
            image_name = docker_names["oj_image_name"]
            needs_image_rebuild = rebuild_decision.oj_image_rebuild_needed
            needs_container_recreate = rebuild_decision.oj_container_recreate_needed
            dockerfile_content = getattr(self.context, 'oj_dockerfile', None)
        else:
            image_name = docker_names["image_name"]
            needs_image_rebuild = rebuild_decision.image_rebuild_needed
            needs_container_recreate = rebuild_decision.container_recreate_needed
            dockerfile_content = getattr(self.context, 'dockerfile', None)
        
        return {
            'container_name': container_name,
            'image_name': image_name,
            'is_oj_container': is_oj_container,
            'needs_image_rebuild': needs_image_rebuild,
            'needs_container_recreate': needs_container_recreate,
            'dockerfile_content': dockerfile_content
        }
    
    def _generate_docker_tasks(self, config: Dict) -> List[PreparationTask]:
        """Generate Docker tasks based on configuration"""
        tasks = []
        
        # Additional compatibility check for existing containers
        if not config['needs_container_recreate']:
            compatible = self.state_manager.inspect_container_compatibility(
                self.operations, config['container_name'], config['image_name']
            )
            if not compatible:
                config['needs_container_recreate'] = True
        
        # Create image build task if needed
        build_task_id = None
        if config['needs_image_rebuild'] and config['dockerfile_content']:
            build_task_id = self._next_task_id("docker_build")
            build_request = DockerRequest(
                op=DockerOpType.BUILD,
                image=config['image_name'],
                dockerfile_text=config['dockerfile_content'],
                options={"t": config['image_name']}
            )
            
            build_task = PreparationTask(
                task_id=build_task_id,
                task_type="docker_build",
                request_object=build_request,
                dependencies=[],
                description=f"Build image: {config['image_name']}",
                parallel_group="docker_preparation"
            )
            tasks.append(build_task)
        
        # Create container remove task if recreation needed
        rebuild_remove_task_id = None
        if config['needs_container_recreate']:
            # Check if container exists first
            docker_driver = self.operations.resolve("docker_driver")
            ps_result = docker_driver.ps(
                all=True, show_output=False, names_only=True
            )
            if config['container_name'] in ps_result:
                rebuild_remove_task_id = self._next_task_id("docker_remove")
                remove_request = DockerRequest(
                    op=DockerOpType.REMOVE,
                    container=config['container_name'],
                    options={"f": ""}  # Force remove flag
                )
                
                remove_task = PreparationTask(
                    task_id=rebuild_remove_task_id,
                    task_type="docker_remove",
                    request_object=remove_request,
                    dependencies=[],
                    description=f"Remove old container: {config['container_name']}",
                    parallel_group="docker_preparation"
                )
                tasks.append(remove_task)
        
        # Create container run task
        run_task_id = self._next_task_id("docker_run")
        run_dependencies = []
        
        # Add dependencies based on what needs to be done first
        if config['needs_image_rebuild'] and build_task_id:
            run_dependencies.append(build_task_id)
        if config['needs_container_recreate'] and rebuild_remove_task_id:
            run_dependencies.append(rebuild_remove_task_id)
        
        # Add volume mount options from env.json
        project_path = self.context.get_project_path()
        volume_options = self.context.get_mount_options(project_path)
        
        # Add container resource limits from env.json
        container_options = self.context.get_container_options()
        volume_options.update(container_options)
        
        run_request = DockerRequest(
            op=DockerOpType.RUN,
            image=config['image_name'],
            container=config['container_name'],
            command=self.context.get_keep_alive_command(),  # From env.json
            options=volume_options
        )
        
        run_task = PreparationTask(
            task_id=run_task_id,
            task_type="docker_run",
            request_object=run_request,
            dependencies=run_dependencies,
            description=f"Run container: {config['container_name']} from image: {config['image_name']}",
            parallel_group="docker_preparation"
        )
        tasks.append(run_task)
        
        return tasks
    
    def _next_task_id(self, prefix: str) -> str:
        """Generate next task ID"""
        self._task_counter += 1
        return f"{prefix}_{self._task_counter:03d}"
    
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