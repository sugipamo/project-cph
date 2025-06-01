"""
Test preparation executor functionality
"""
import pytest
from unittest.mock import MagicMock, patch

from src.env_integration.fitting.preparation_executor import (
    PreparationExecutor, PreparationTask
)
from src.env_integration.fitting.environment_inspector import (
    ResourceStatus, ResourceType
)
from src.context.execution_context import ExecutionContext
from src.operations.docker.docker_request import DockerRequest
from src.operations.file.file_request import FileRequest


class TestPreparationExecutor:
    """Test PreparationExecutor class"""
    
    def setup_method(self):
        """Setup test environment"""
        self.mock_operations = MagicMock()
        self.mock_context = MagicMock(spec=ExecutionContext)
        
        # Mock Docker names  
        self.mock_context.get_docker_names.return_value = {
            "image_name": "python",
            "container_name": "cph_python",
            "oj_image_name": "ojtools",
            "oj_container_name": "cph_ojtools"
        }
        
        # Mock basic context attributes needed by DockerStateManager
        self.mock_context.language = "python"
        self.mock_context.env_type = "docker"
        self.mock_context.dockerfile_resolver = None  # No resolver for simple tests
        
        # Mock docker driver for ps command
        self.mock_docker_driver = MagicMock()
        self.mock_operations.resolve.return_value = self.mock_docker_driver
        self.mock_docker_driver.ps.return_value = []  # No containers exist
        
        self.executor = PreparationExecutor(self.mock_operations, self.mock_context)
    
    def test_create_docker_run_task(self):
        """Test creation of Docker run task"""
        tasks = self.executor._create_docker_run_task("cph_python")
        
        # Should return a list of tasks
        assert isinstance(tasks, list)
        assert len(tasks) >= 1
        
        # Find the run task
        run_task = None
        for task in tasks:
            if task.task_type == "docker_run":
                run_task = task
                break
        
        assert run_task is not None
        assert run_task.description == "Run container: cph_python from image: python"
        assert isinstance(run_task.request_object, DockerRequest)
        assert run_task.request_object.op.name == "RUN"
        assert run_task.request_object.image == "python"
        assert run_task.request_object.container == "cph_python"
    
    def test_create_docker_run_task_oj(self):
        """Test creation of OJ Docker run task"""
        task = self.executor._create_docker_run_task("cph_ojtools")
        
        assert task.task_type == "docker_run"
        assert task.description == "Run container: cph_ojtools from image: ojtools"
        assert task.request_object.image == "ojtools"
        assert task.request_object.container == "cph_ojtools"
    
    def test_create_docker_remove_task(self):
        """Test creation of Docker remove task"""
        task = self.executor._create_docker_remove_task("cph_python")
        
        assert task.task_type == "docker_remove"
        assert task.description == "Remove stopped container: cph_python"
        assert isinstance(task.request_object, DockerRequest)
        assert task.dependencies == []
        assert task.request_object.op.name == "REMOVE"
        assert task.request_object.container == "cph_python"
    
    def test_create_mkdir_preparation_task(self):
        """Test creation of mkdir preparation task"""
        status = ResourceStatus(
            resource_type=ResourceType.DIRECTORY,
            identifier="/workspace",
            current_state="missing",
            exists=False,
            needs_preparation=True,
            preparation_actions=["create_directory"]
        )
        
        task = self.executor._create_mkdir_preparation_task("/workspace", status)
        
        assert task is not None
        assert task.task_type == "mkdir"
        assert task.description == "Create directory: /workspace"
        assert isinstance(task.request_object, FileRequest)
        assert task.dependencies == []
        assert task.request_object.op.name == "MKDIR"
        assert task.request_object.path == "/workspace"
    
    def test_create_mkdir_preparation_task_no_action(self):
        """Test mkdir task creation when no action needed"""
        status = ResourceStatus(
            resource_type=ResourceType.DIRECTORY,
            identifier="/workspace",
            current_state="exists",
            exists=True,
            needs_preparation=False,
            preparation_actions=[]
        )
        
        task = self.executor._create_mkdir_preparation_task("/workspace", status)
        
        assert task is None
    
    def test_create_container_preparation_tasks_stopped(self):
        """Test container preparation for stopped container"""
        status = ResourceStatus(
            resource_type=ResourceType.DOCKER_CONTAINER,
            identifier="cph_python",
            current_state="stopped",
            exists=True,
            needs_preparation=True,
            preparation_actions=["remove_stopped_container", "run_new_container"]
        )
        
        tasks = self.executor._create_container_preparation_tasks("cph_python", status)
        
        assert len(tasks) == 2
        
        # First task should be remove
        remove_task = tasks[0]
        assert remove_task.task_type == "docker_remove"
        assert remove_task.dependencies == []
        
        # Second task should be run with dependency on remove
        run_task = tasks[1]
        assert run_task.task_type == "docker_run"
        assert run_task.dependencies == [remove_task.task_id]
    
    def test_create_container_preparation_tasks_missing(self):
        """Test container preparation for missing container"""
        status = ResourceStatus(
            resource_type=ResourceType.DOCKER_CONTAINER,
            identifier="cph_python",
            current_state="missing",
            exists=False,
            needs_preparation=True,
            preparation_actions=["run_new_container"]
        )
        
        tasks = self.executor._create_container_preparation_tasks("cph_python", status)
        
        assert len(tasks) == 1
        run_task = tasks[0]
        assert run_task.task_type == "docker_run"
        assert run_task.dependencies == []
    
    def test_generate_preparation_tasks_parallel_groups(self):
        """Test generation of preparation tasks with parallel groups"""
        statuses = {
            "cph_python": ResourceStatus(
                resource_type=ResourceType.DOCKER_CONTAINER,
                identifier="cph_python",
                current_state="missing",
                exists=False,
                needs_preparation=True,
                preparation_actions=["run_new_container"]
            ),
            "/workspace": ResourceStatus(
                resource_type=ResourceType.DIRECTORY,
                identifier="/workspace",
                current_state="missing",
                exists=False,
                needs_preparation=True,
                preparation_actions=["create_directory"]
            )
        }
        
        tasks = self.executor._generate_preparation_tasks(statuses)
        
        # Should have one docker task and one mkdir task
        docker_tasks = [t for t in tasks if t.task_type == "docker_run"]
        mkdir_tasks = [t for t in tasks if t.task_type == "mkdir"]
        
        assert len(docker_tasks) == 1
        assert len(mkdir_tasks) == 1
        
        # Check parallel groups
        assert docker_tasks[0].parallel_group == "docker_preparation"
        assert mkdir_tasks[0].parallel_group == "mkdir_preparation"
    
    def test_sort_tasks_by_dependencies(self):
        """Test task sorting by dependencies"""
        task1 = PreparationTask(
            task_id="remove_001",
            task_type="docker_remove",
            request_object=MagicMock(),
            dependencies=[],
            description="Remove task"
        )
        
        task2 = PreparationTask(
            task_id="run_001",
            task_type="docker_run",
            request_object=MagicMock(),
            dependencies=["remove_001"],
            description="Run task"
        )
        
        task3 = PreparationTask(
            task_id="mkdir_001",
            task_type="mkdir",
            request_object=MagicMock(),
            dependencies=[],
            description="Mkdir task",
            parallel_group="mkdir_preparation"
        )
        
        # Tasks in wrong order
        tasks = [task2, task3, task1]
        
        sorted_tasks = self.executor._sort_tasks_by_dependencies(tasks)
        
        # Should have dependencies resolved
        task_ids = [t.task_id for t in sorted_tasks]
        
        # mkdir task can be anywhere (no dependencies)
        # remove task must come before run task
        remove_index = task_ids.index("remove_001")
        run_index = task_ids.index("run_001")
        
        assert remove_index < run_index
    
    def test_convert_to_workflow_requests(self):
        """Test conversion of preparation tasks to workflow requests"""
        task1 = PreparationTask(
            task_id="mkdir_001",
            task_type="mkdir",
            request_object=MagicMock(),
            dependencies=[],
            description="Mkdir task"
        )
        
        task2 = PreparationTask(
            task_id="docker_001",
            task_type="docker_run",
            request_object=MagicMock(),
            dependencies=[],
            description="Docker task"
        )
        
        tasks = [task1, task2]
        
        requests = self.executor.convert_to_workflow_requests(tasks)
        
        assert len(requests) == 2
        assert requests[0] == task1.request_object
        assert requests[1] == task2.request_object
    
    def test_analyze_and_prepare_integration(self):
        """Test full analyze and prepare workflow"""
        # Mock workflow tasks with docker exec
        workflow_tasks = [
            {"command": "docker exec cph_python python main.py"}
        ]
        
        # Mock inspector methods directly through the executor's inspector
        with patch.object(self.executor.inspector, 'extract_requirements_from_workflow_tasks') as mock_extract:
            with patch.object(self.executor.inspector, 'inspect_docker_containers') as mock_docker:
                with patch.object(self.executor.inspector, 'inspect_directories') as mock_dirs:
                    
                    # Setup mock returns
                    mock_extract.return_value = []
                    mock_docker.return_value = {}
                    mock_dirs.return_value = {}
                    
                    tasks, statuses = self.executor.analyze_and_prepare(workflow_tasks)
                    
                    # Should call inspector methods
                    mock_extract.assert_called_once_with(workflow_tasks)
                    
                    assert isinstance(tasks, list)
                    assert isinstance(statuses, dict)