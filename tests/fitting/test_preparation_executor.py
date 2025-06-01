"""
Test preparation executor functionality
"""
import pytest
from unittest.mock import MagicMock, patch

from src.env_integration.fitting.preparation_executor import (
    PreparationExecutor, PreparationTask, ContainerConfig,
    _determine_container_config, _generate_docker_tasks, _update_container_state
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
        tasks = self.executor._create_docker_run_task("cph_ojtools")
        
        # Should return a list of tasks, find the run task
        assert isinstance(tasks, list)
        assert len(tasks) > 0
        
        # Find the docker_run task
        run_task = next((task for task in tasks if task.task_type == "docker_run"), None)
        assert run_task is not None
        assert run_task.description.startswith("Run container: cph_ojtools from image:")
        assert run_task.request_object.container == "cph_ojtools"
    
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
        
        # Mock DockerStateManager to indicate no rebuild needed
        with patch.object(self.executor.state_manager, 'check_rebuild_needed', return_value=(False, False, False, False)):
            tasks = self.executor._create_container_preparation_tasks("cph_python", status)
        
        assert len(tasks) == 2
        
        # First task should be remove
        remove_task = tasks[0]
        assert remove_task.task_type == "docker_remove"
        assert remove_task.dependencies == []
        
        # Second task should be run with dependency on remove
        run_task = tasks[1]
        assert run_task.task_type == "docker_run"
        assert remove_task.task_id in run_task.dependencies
    
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
        
        # Mock DockerStateManager to indicate no rebuild needed
        with patch.object(self.executor.state_manager, 'check_rebuild_needed', return_value=(False, False, False, False)):
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


class TestPureFunctions:
    """Test pure functions extracted from PreparationExecutor"""

    def test_determine_container_config_regular_container(self):
        """Test _determine_container_config for regular container"""
        # Setup mock context
        mock_context = MagicMock()
        mock_context.get_docker_names.return_value = {
            "image_name": "python:3.10",
            "container_name": "cph_python",
            "oj_image_name": "ojtools:latest",
            "oj_container_name": "cph_ojtools"
        }
        mock_context.dockerfile = "FROM python:3.10\nRUN pip install ..."
        mock_context.oj_dockerfile = "FROM ubuntu:20.04\nRUN apt-get ..."

        # Setup mock state manager
        mock_state_manager = MagicMock()
        mock_state_manager.check_rebuild_needed.return_value = (True, False, True, False)

        # Test regular container
        config = _determine_container_config("cph_python", mock_context, mock_state_manager)

        assert config.container_name == "cph_python"
        assert config.image_name == "python:3.10"
        assert config.is_oj_container == False
        assert config.needs_image_rebuild == True
        assert config.needs_container_recreate == True
        assert config.dockerfile_content == "FROM python:3.10\nRUN pip install ..."

    def test_determine_container_config_oj_container(self):
        """Test _determine_container_config for OJ container"""
        # Setup mock context
        mock_context = MagicMock()
        mock_context.get_docker_names.return_value = {
            "image_name": "python:3.10",
            "container_name": "cph_python",
            "oj_image_name": "ojtools:latest",
            "oj_container_name": "cph_ojtools"
        }
        mock_context.dockerfile = "FROM python:3.10\nRUN pip install ..."
        mock_context.oj_dockerfile = "FROM ubuntu:20.04\nRUN apt-get ..."

        # Setup mock state manager
        mock_state_manager = MagicMock()
        mock_state_manager.check_rebuild_needed.return_value = (False, True, False, True)

        # Test OJ container
        config = _determine_container_config("cph_ojtools_test", mock_context, mock_state_manager)

        assert config.container_name == "cph_ojtools_test"
        assert config.image_name == "ojtools:latest"
        assert config.is_oj_container == True
        assert config.needs_image_rebuild == True
        assert config.needs_container_recreate == True
        assert config.dockerfile_content == "FROM ubuntu:20.04\nRUN apt-get ..."

    def test_generate_docker_tasks_no_rebuild_needed(self):
        """Test _generate_docker_tasks when no rebuild needed"""
        config = ContainerConfig(
            container_name="test_container",
            image_name="test_image",
            is_oj_container=False,
            needs_image_rebuild=False,
            needs_container_recreate=False,
            dockerfile_content="FROM python:3.10"
        )

        # Mock task ID generator
        task_counter = [0]
        def mock_task_id_generator(prefix):
            task_counter[0] += 1
            return f"{prefix}_{task_counter[0]:03d}"

        # Mock operations and state manager
        mock_operations = MagicMock()
        mock_docker_driver = MagicMock()
        mock_docker_driver.ps.return_value = []  # No existing containers
        mock_operations.resolve.return_value = mock_docker_driver

        mock_state_manager = MagicMock()
        mock_state_manager.inspect_container_compatibility.return_value = True

        tasks = _generate_docker_tasks(config, mock_task_id_generator, mock_operations, mock_state_manager)

        # Should only have run task
        assert len(tasks) == 1
        assert tasks[0].task_type == "docker_run"
        assert tasks[0].dependencies == []

    def test_generate_docker_tasks_full_rebuild(self):
        """Test _generate_docker_tasks with full rebuild needed"""
        config = ContainerConfig(
            container_name="test_container",
            image_name="test_image",
            is_oj_container=False,
            needs_image_rebuild=True,
            needs_container_recreate=True,
            dockerfile_content="FROM python:3.10\nRUN pip install requests"
        )

        # Mock task ID generator
        task_counter = [0]
        def mock_task_id_generator(prefix):
            task_counter[0] += 1
            return f"{prefix}_{task_counter[0]:03d}"

        # Mock operations and state manager
        mock_operations = MagicMock()
        mock_docker_driver = MagicMock()
        mock_docker_driver.ps.return_value = ["test_container"]  # Container exists
        mock_operations.resolve.return_value = mock_docker_driver

        mock_state_manager = MagicMock()
        mock_state_manager.inspect_container_compatibility.return_value = False

        tasks = _generate_docker_tasks(config, mock_task_id_generator, mock_operations, mock_state_manager)

        # Should have build, remove, and run tasks
        task_types = [t.task_type for t in tasks]
        assert "docker_build" in task_types
        assert "docker_remove" in task_types
        assert "docker_run" in task_types

        # Verify dependencies
        build_task = next(t for t in tasks if t.task_type == "docker_build")
        remove_task = next(t for t in tasks if t.task_type == "docker_remove")
        run_task = next(t for t in tasks if t.task_type == "docker_run")

        assert build_task.dependencies == []
        assert remove_task.dependencies == []
        assert build_task.task_id in run_task.dependencies
        assert remove_task.task_id in run_task.dependencies

    def test_generate_docker_tasks_image_build_only(self):
        """Test _generate_docker_tasks with image build only"""
        config = ContainerConfig(
            container_name="test_container",
            image_name="test_image",
            is_oj_container=False,
            needs_image_rebuild=True,
            needs_container_recreate=False,
            dockerfile_content="FROM python:3.10"
        )

        task_counter = [0]
        def mock_task_id_generator(prefix):
            task_counter[0] += 1
            return f"{prefix}_{task_counter[0]:03d}"

        mock_operations = MagicMock()
        mock_docker_driver = MagicMock()
        mock_docker_driver.ps.return_value = []
        mock_operations.resolve.return_value = mock_docker_driver

        mock_state_manager = MagicMock()
        mock_state_manager.inspect_container_compatibility.return_value = True

        tasks = _generate_docker_tasks(config, mock_task_id_generator, mock_operations, mock_state_manager)

        # Should have build and run tasks
        task_types = [t.task_type for t in tasks]
        assert "docker_build" in task_types
        assert "docker_run" in task_types
        assert "docker_remove" not in task_types

        # Verify dependencies
        build_task = next(t for t in tasks if t.task_type == "docker_build")
        run_task = next(t for t in tasks if t.task_type == "docker_run")

        assert build_task.task_id in run_task.dependencies

    def test_generate_docker_tasks_no_dockerfile(self):
        """Test _generate_docker_tasks with no dockerfile content"""
        config = ContainerConfig(
            container_name="test_container",
            image_name="test_image",
            is_oj_container=False,
            needs_image_rebuild=True,
            needs_container_recreate=False,
            dockerfile_content=None
        )

        task_counter = [0]
        def mock_task_id_generator(prefix):
            task_counter[0] += 1
            return f"{prefix}_{task_counter[0]:03d}"

        mock_operations = MagicMock()
        mock_docker_driver = MagicMock()
        mock_docker_driver.ps.return_value = []
        mock_operations.resolve.return_value = mock_docker_driver

        mock_state_manager = MagicMock()
        mock_state_manager.inspect_container_compatibility.return_value = True

        tasks = _generate_docker_tasks(config, mock_task_id_generator, mock_operations, mock_state_manager)

        # Should only have run task (no build without dockerfile)
        task_types = [t.task_type for t in tasks]
        assert "docker_build" not in task_types
        assert "docker_run" in task_types

    def test_update_container_state(self):
        """Test _update_container_state function"""
        mock_state_manager = MagicMock()
        mock_context = MagicMock()

        _update_container_state(mock_state_manager, mock_context)

        mock_state_manager.update_state.assert_called_once_with(mock_context)


class TestContainerConfig:
    """Test ContainerConfig dataclass"""

    def test_container_config_creation(self):
        """Test creating ContainerConfig instance"""
        config = ContainerConfig(
            container_name="test_container",
            image_name="test_image:latest",
            is_oj_container=True,
            needs_image_rebuild=False,
            needs_container_recreate=True,
            dockerfile_content="FROM ubuntu"
        )

        assert config.container_name == "test_container"
        assert config.image_name == "test_image:latest"
        assert config.is_oj_container == True
        assert config.needs_image_rebuild == False
        assert config.needs_container_recreate == True
        assert config.dockerfile_content == "FROM ubuntu"

    def test_container_config_default_dockerfile(self):
        """Test ContainerConfig with default dockerfile content"""
        config = ContainerConfig(
            container_name="test_container",
            image_name="test_image",
            is_oj_container=False,
            needs_image_rebuild=True,
            needs_container_recreate=False
        )

        assert config.dockerfile_content is None


class TestEdgeCases:
    """Test edge cases for pure functions"""

    def test_determine_container_config_edge_container_name(self):
        """Test edge cases for container name patterns"""
        mock_context = MagicMock()
        mock_context.get_docker_names.return_value = {
            "image_name": "python",
            "oj_image_name": "ojtools"
        }
        mock_context.dockerfile = "FROM python"
        mock_context.oj_dockerfile = "FROM ubuntu"

        mock_state_manager = MagicMock()
        mock_state_manager.check_rebuild_needed.return_value = (False, False, False, False)

        # Test edge case: container name starts with "cph_ojtools"
        config = _determine_container_config("cph_ojtools_test", mock_context, mock_state_manager)
        assert config.is_oj_container == True

        # Test edge case: container name exactly matches prefix
        config = _determine_container_config("cph_ojtools", mock_context, mock_state_manager)
        assert config.is_oj_container == True

        # Test edge case: similar but different prefix
        config = _determine_container_config("cph_other", mock_context, mock_state_manager)
        assert config.is_oj_container == False

        # Test edge case: substring but not prefix
        config = _determine_container_config("my_cph_ojtools_test", mock_context, mock_state_manager)
        assert config.is_oj_container == False

    def test_generate_docker_tasks_compatibility_check_override(self):
        """Test compatibility check overriding needs_container_recreate"""
        config = ContainerConfig(
            container_name="test_container",
            image_name="test_image",
            is_oj_container=False,
            needs_image_rebuild=False,
            needs_container_recreate=False,  # Initially False
            dockerfile_content=None
        )

        task_counter = [0]
        def mock_task_id_generator(prefix):
            task_counter[0] += 1
            return f"{prefix}_{task_counter[0]:03d}"

        mock_operations = MagicMock()
        mock_docker_driver = MagicMock()
        mock_docker_driver.ps.return_value = ["test_container"]  # Container exists
        mock_operations.resolve.return_value = mock_docker_driver

        mock_state_manager = MagicMock()
        mock_state_manager.inspect_container_compatibility.return_value = False  # Incompatible

        tasks = _generate_docker_tasks(config, mock_task_id_generator, mock_operations, mock_state_manager)

        # Should now include remove task due to compatibility check
        task_types = [t.task_type for t in tasks]
        assert "docker_remove" in task_types
        assert "docker_run" in task_types

    def test_generate_docker_tasks_empty_container_list(self):
        """Test _generate_docker_tasks when container list is empty"""
        config = ContainerConfig(
            container_name="test_container",
            image_name="test_image",
            is_oj_container=False,
            needs_image_rebuild=False,
            needs_container_recreate=True,
            dockerfile_content=None
        )

        task_counter = [0]
        def mock_task_id_generator(prefix):
            task_counter[0] += 1
            return f"{prefix}_{task_counter[0]:03d}"

        mock_operations = MagicMock()
        mock_docker_driver = MagicMock()
        mock_docker_driver.ps.return_value = []  # Empty container list
        mock_operations.resolve.return_value = mock_docker_driver

        mock_state_manager = MagicMock()
        mock_state_manager.inspect_container_compatibility.return_value = True

        tasks = _generate_docker_tasks(config, mock_task_id_generator, mock_operations, mock_state_manager)

        # Should not include remove task since no container exists
        task_types = [t.task_type for t in tasks]
        assert "docker_remove" not in task_types
        assert "docker_run" in task_types

    def test_determine_container_config_boundary_values(self):
        """Test _determine_container_config with boundary values"""
        mock_context = MagicMock()
        mock_context.get_docker_names.return_value = {
            "image_name": "",  # Empty string
            "oj_image_name": ""
        }
        mock_context.dockerfile = ""  # Empty dockerfile
        mock_context.oj_dockerfile = None  # None dockerfile

        mock_state_manager = MagicMock()
        mock_state_manager.check_rebuild_needed.return_value = (True, True, True, True)

        # Test with empty strings
        config = _determine_container_config("", mock_context, mock_state_manager)
        assert config.container_name == ""
        assert config.image_name == ""
        assert config.is_oj_container == False
        assert config.dockerfile_content == ""

        # Test with None-like container name
        config = _determine_container_config("cph_ojtools", mock_context, mock_state_manager)
        assert config.is_oj_container == True
        assert config.dockerfile_content is None

    def test_generate_docker_tasks_task_id_uniqueness(self):
        """Test that task IDs are unique across multiple calls"""
        config = ContainerConfig(
            container_name="test_container",
            image_name="test_image",
            is_oj_container=False,
            needs_image_rebuild=True,
            needs_container_recreate=True,
            dockerfile_content="FROM python"
        )

        task_counter = [0]
        def mock_task_id_generator(prefix):
            task_counter[0] += 1
            return f"{prefix}_{task_counter[0]:03d}"

        mock_operations = MagicMock()
        mock_docker_driver = MagicMock()
        mock_docker_driver.ps.return_value = ["test_container"]
        mock_operations.resolve.return_value = mock_docker_driver

        mock_state_manager = MagicMock()
        mock_state_manager.inspect_container_compatibility.return_value = False

        tasks = _generate_docker_tasks(config, mock_task_id_generator, mock_operations, mock_state_manager)

        # Verify all task IDs are unique
        task_ids = [t.task_id for t in tasks]
        assert len(task_ids) == len(set(task_ids))  # No duplicates

        # Verify task ID format
        for task_id in task_ids:
            assert "_" in task_id
            assert task_id.split("_")[-1].isdigit()  # Ends with number

    def test_generate_docker_tasks_mutable_config(self):
        """Test that _generate_docker_tasks can modify config.needs_container_recreate"""
        config = ContainerConfig(
            container_name="test_container",
            image_name="test_image",
            is_oj_container=False,
            needs_image_rebuild=False,
            needs_container_recreate=False,
            dockerfile_content=None
        )

        original_recreate = config.needs_container_recreate

        task_counter = [0]
        def mock_task_id_generator(prefix):
            task_counter[0] += 1
            return f"{prefix}_{task_counter[0]:03d}"

        mock_operations = MagicMock()
        mock_docker_driver = MagicMock()
        mock_docker_driver.ps.return_value = ["test_container"]
        mock_operations.resolve.return_value = mock_docker_driver

        mock_state_manager = MagicMock()
        mock_state_manager.inspect_container_compatibility.return_value = False

        tasks = _generate_docker_tasks(config, mock_task_id_generator, mock_operations, mock_state_manager)

        # Config should be modified due to compatibility check
        assert config.needs_container_recreate != original_recreate
        assert config.needs_container_recreate == True

        # Should include remove task
        task_types = [t.task_type for t in tasks]
        assert "docker_remove" in task_types