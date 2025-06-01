"""
Integration test for workflow and fitting functionality
"""
import pytest
from unittest.mock import MagicMock, patch

from src.env_core.step.step import Step, StepType
from src.env_core.workflow.pure_request_factory import PureRequestFactory
from src.env_integration.fitting.preparation_executor import PreparationExecutor
from src.env_integration.fitting.environment_inspector import EnvironmentInspector
from src.context.execution_context import ExecutionContext
from src.operations.docker.docker_request import DockerRequest, DockerOpType
from src.operations.file.file_request import FileRequest


class TestWorkflowFittingIntegration:
    """Test integration between workflow generation and fitting preparation"""
    
    def setup_method(self):
        """Setup test environment"""
        self.mock_operations = MagicMock()
        self.mock_docker_driver = MagicMock()
        self.mock_file_driver = MagicMock()
        
        self.mock_operations.resolve.side_effect = lambda driver_type: {
            "docker_driver": self.mock_docker_driver,
            "file_driver": self.mock_file_driver
        }[driver_type]
        
        # Mock context
        self.mock_context = MagicMock(spec=ExecutionContext)
        self.mock_context.get_docker_names.return_value = {
            "image_name": "python_test",
            "container_name": "cph_python_test",
            "oj_image_name": "ojtools_test",
            "oj_container_name": "cph_ojtools_test"
        }
        self.mock_context.language = "python"
        
        # Setup dockerfile_resolver properly
        mock_dockerfile_resolver = MagicMock()
        mock_dockerfile_resolver.dockerfile = "FROM python:3.9\nRUN pip install requests"
        mock_dockerfile_resolver.oj_dockerfile = None
        self.mock_context.dockerfile_resolver = mock_dockerfile_resolver
        
        self.executor = PreparationExecutor(self.mock_operations, self.mock_context)
    
    def test_docker_exec_workflow_with_fitting(self):
        """Test workflow with docker exec that requires container preparation"""
        # Create workflow steps that include docker exec
        workflow_steps = [
            Step(
                type=StepType.DOCKER_EXEC,
                cmd=["cph_python_test", "python", "main.py"],
                show_output=True
            )
        ]
        
        # Mock environment state - container is missing
        self.mock_docker_driver.ps.return_value = []  # No containers exist
        
        # Mock file operations for directory check
        mock_file_result = MagicMock()
        mock_file_result.success = True
        mock_file_result.exists = True
        self.mock_file_driver.execute.return_value = mock_file_result
        
        # Convert steps to workflow tasks
        workflow_tasks = []
        for step in workflow_steps:
            request = PureRequestFactory.create_request_from_step(step, self.mock_context)
            workflow_tasks.append({
                "request_object": request,
                "command": f"docker exec {step.cmd[0]} {' '.join(step.cmd[1:])}",
                "request_type": "docker"
            })
        
        # Analyze and prepare
        preparation_tasks, statuses = self.executor.analyze_and_prepare(workflow_tasks)
        
        # Should generate container preparation task
        assert len(preparation_tasks) >= 1
        docker_tasks = [t for t in preparation_tasks if t.task_type == "docker_run"]
        assert len(docker_tasks) == 1
        
        # Check the docker run task
        docker_task = docker_tasks[0]
        assert docker_task.description == "Run container: cph_python_test from image: python_test"
        assert isinstance(docker_task.request_object, DockerRequest)
        assert docker_task.request_object.op == DockerOpType.RUN
        assert docker_task.request_object.image == "python_test"
        assert docker_task.request_object.container == "cph_python_test"
    
    def test_docker_cp_workflow_with_fitting(self):
        """Test workflow with docker cp that requires container and directory preparation"""
        # Create workflow steps that include docker cp
        workflow_steps = [
            Step(
                type=StepType.DOCKER_CP,
                cmd=["/local/file.py", "cph_python_test:/workspace/file.py"]
            )
        ]
        
        # Mock environment state - container missing, directory missing
        self.mock_docker_driver.ps.return_value = []  # No containers
        
        # Mock file operations - directory doesn't exist
        mock_file_result = MagicMock()
        mock_file_result.success = True
        mock_file_result.exists = False
        self.mock_file_driver.execute.return_value = mock_file_result
        
        # Convert steps to workflow tasks
        workflow_tasks = []
        for step in workflow_steps:
            request = PureRequestFactory.create_request_from_step(step, self.mock_context)
            workflow_tasks.append({
                "request_object": request,
                "command": f"docker cp {step.cmd[0]} {step.cmd[1]}",
                "request_type": "docker"
            })
        
        # Analyze and prepare
        preparation_tasks, statuses = self.executor.analyze_and_prepare(workflow_tasks)
        
        # Should generate both container and directory preparation tasks
        docker_tasks = [t for t in preparation_tasks if t.task_type == "docker_run"]
        mkdir_tasks = [t for t in preparation_tasks if t.task_type == "mkdir"]
        
        assert len(docker_tasks) == 1
        assert len(mkdir_tasks) == 1
        
        # Check tasks are in parallel groups
        assert docker_tasks[0].parallel_group == "docker_preparation"
        assert mkdir_tasks[0].parallel_group == "mkdir_preparation"
        
        # Check mkdir task
        mkdir_task = mkdir_tasks[0]
        assert mkdir_task.description == "Create directory: /workspace"
        assert isinstance(mkdir_task.request_object, FileRequest)
    
    def test_complex_workflow_with_multiple_docker_operations(self):
        """Test complex workflow with multiple Docker operations"""
        # Create complex workflow
        workflow_steps = [
            Step(
                type=StepType.MKDIR,
                cmd=["/local/workspace"]
            ),
            Step(
                type=StepType.DOCKER_CP,
                cmd=["/local/workspace/source.py", "cph_python_test:/app/source.py"]
            ),
            Step(
                type=StepType.DOCKER_EXEC,
                cmd=["cph_python_test", "python", "/app/source.py"]
            ),
            Step(
                type=StepType.DOCKER_CP,
                cmd=["cph_python_test:/app/output.txt", "/local/workspace/output.txt"]
            )
        ]
        
        # Mock environment state
        self.mock_docker_driver.ps.return_value = []  # Container missing
        
        # Mock file operations
        mock_file_result = MagicMock()
        mock_file_result.success = True
        mock_file_result.exists = False  # Directories don't exist
        self.mock_file_driver.execute.return_value = mock_file_result
        
        # Convert steps to workflow tasks
        workflow_tasks = []
        for step in workflow_steps:
            request = PureRequestFactory.create_request_from_step(step, self.mock_context)
            if step.type in [StepType.DOCKER_EXEC, StepType.DOCKER_CP]:
                command = f"docker {step.type.value.split('_')[1]} {' '.join(step.cmd)}"
            else:
                command = f"{step.type.value} {' '.join(step.cmd)}"
            
            workflow_tasks.append({
                "request_object": request,
                "command": command,
                "request_type": "docker" if step.type.value.startswith("docker") else "file"
            })
        
        # Analyze and prepare
        preparation_tasks, statuses = self.executor.analyze_and_prepare(workflow_tasks)
        
        # Should generate preparation for container and directories
        docker_tasks = [t for t in preparation_tasks if t.task_type == "docker_run"]
        mkdir_tasks = [t for t in preparation_tasks if t.task_type == "mkdir"]
        
        # Should prepare container once
        assert len(docker_tasks) == 1
        
        # Should prepare directories needed for Docker cp
        assert len(mkdir_tasks) >= 1
        
        # Convert to workflow requests
        preparation_requests = self.executor.convert_to_workflow_requests(preparation_tasks)
        
        # Should have both docker and file requests
        docker_prep_requests = [r for r in preparation_requests if isinstance(r, DockerRequest)]
        file_prep_requests = [r for r in preparation_requests if isinstance(r, FileRequest)]
        
        assert len(docker_prep_requests) >= 1
        assert len(file_prep_requests) >= 1
    
    def test_no_preparation_needed_scenario(self):
        """Test scenario where no preparation is needed"""
        # Create workflow steps
        workflow_steps = [
            Step(
                type=StepType.DOCKER_EXEC,
                cmd=["cph_python_test", "echo", "hello"]
            )
        ]
        
        # Mock environment state - everything exists and is ready
        self.mock_docker_driver.ps.return_value = ["/cph_python_test"]  # Container exists
        self.mock_docker_driver.inspect.return_value = {
            "State": {"Status": "running"}
        }
        
        # Convert steps to workflow tasks
        workflow_tasks = []
        for step in workflow_steps:
            request = PureRequestFactory.create_request_from_step(step, self.mock_context)
            workflow_tasks.append({
                "request_object": request,
                "command": f"docker exec {step.cmd[0]} {' '.join(step.cmd[1:])}",
                "request_type": "docker"
            })
        
        # Analyze and prepare
        preparation_tasks, statuses = self.executor.analyze_and_prepare(workflow_tasks)
        
        # Should not generate any preparation tasks
        assert len(preparation_tasks) == 0
        
        # Status should indicate no preparation needed
        assert "cph_python_test" in statuses
        container_status = statuses["cph_python_test"]
        assert container_status.needs_preparation is False
        assert container_status.current_state == "running"
    
    def test_stopped_container_preparation(self):
        """Test preparation for stopped container"""
        # Create workflow steps
        workflow_steps = [
            Step(
                type=StepType.DOCKER_EXEC,
                cmd=["cph_python_test", "python", "--version"]
            )
        ]
        
        # Mock environment state - container exists but stopped
        self.mock_docker_driver.ps.return_value = ["/cph_python_test"]
        self.mock_docker_driver.inspect.return_value = {
            "State": {"Status": "exited"}
        }
        
        # Convert steps to workflow tasks
        workflow_tasks = []
        for step in workflow_steps:
            request = PureRequestFactory.create_request_from_step(step, self.mock_context)
            workflow_tasks.append({
                "request_object": request,
                "command": f"docker exec {step.cmd[0]} {' '.join(step.cmd[1:])}",
                "request_type": "docker"
            })
        
        # Analyze and prepare
        preparation_tasks, statuses = self.executor.analyze_and_prepare(workflow_tasks)
        
        # Should generate remove and run tasks
        remove_tasks = [t for t in preparation_tasks if t.task_type == "docker_remove"]
        run_tasks = [t for t in preparation_tasks if t.task_type == "docker_run"]
        
        assert len(remove_tasks) == 1
        assert len(run_tasks) == 1
        
        # Run task should depend on remove task
        run_task = run_tasks[0]
        remove_task = remove_tasks[0]
        assert remove_task.task_id in run_task.dependencies
        
        # Status should indicate preparation needed
        container_status = statuses["cph_python_test"]
        assert container_status.needs_preparation is True
        assert container_status.current_state == "stopped"
    
    def test_oj_tools_container_preparation(self):
        """Test preparation for OJ tools container"""
        # Update context for OJ tools
        self.mock_context.get_docker_names.return_value = {
            "image_name": "python_test",
            "container_name": "cph_python_test",
            "oj_image_name": "ojtools_test",
            "oj_container_name": "cph_ojtools_test"
        }
        
        # Create workflow steps using OJ tools
        workflow_steps = [
            Step(
                type=StepType.DOCKER_EXEC,
                cmd=["cph_ojtools_test", "oj", "test", "-c", "python3 main.py"]
            )
        ]
        
        # Mock environment state - OJ container missing
        self.mock_docker_driver.ps.return_value = []
        
        # Convert steps to workflow tasks
        workflow_tasks = []
        for step in workflow_steps:
            request = PureRequestFactory.create_request_from_step(step, self.mock_context)
            workflow_tasks.append({
                "request_object": request,
                "command": f"docker exec {step.cmd[0]} {' '.join(step.cmd[1:])}",
                "request_type": "docker"
            })
        
        # Analyze and prepare
        preparation_tasks, statuses = self.executor.analyze_and_prepare(workflow_tasks)
        
        # Should generate OJ container preparation
        docker_tasks = [t for t in preparation_tasks if t.task_type == "docker_run"]
        assert len(docker_tasks) == 1
        
        docker_task = docker_tasks[0]
        assert docker_task.description == "Run container: cph_ojtools_test from image: ojtools_test"
        assert docker_task.request_object.image == "ojtools_test"
        assert docker_task.request_object.container == "cph_ojtools_test"