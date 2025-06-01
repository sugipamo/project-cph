"""
Test environment inspector functionality
"""
import pytest
from unittest.mock import MagicMock, patch

from src.env_integration.fitting.environment_inspector import (
    EnvironmentInspector, ResourceType, ResourceStatus, ResourceRequirement
)
from src.operations.result.docker_result import DockerResult
from src.operations.result.file_result import FileResult


class TestEnvironmentInspector:
    """Test EnvironmentInspector class"""
    
    def setup_method(self):
        """Setup test environment"""
        self.mock_operations = MagicMock()
        self.mock_docker_driver = MagicMock()
        self.mock_file_driver = MagicMock()
        
        self.mock_operations.resolve.side_effect = lambda driver_type: {
            "docker_driver": self.mock_docker_driver,
            "file_driver": self.mock_file_driver
        }[driver_type]
        
        self.inspector = EnvironmentInspector(self.mock_operations)
    
    def test_inspect_docker_containers_running(self):
        """Test inspection of running Docker containers"""
        # Mock docker driver methods directly
        self.mock_docker_driver.ps.return_value = ["/cph_python"]
        self.mock_docker_driver.inspect.return_value = {
            "State": {"Status": "running"}
        }
        
        result = self.inspector.inspect_docker_containers(["cph_python"])
        
        assert "cph_python" in result
        status = result["cph_python"]
        assert status.resource_type == ResourceType.DOCKER_CONTAINER
        assert status.current_state == "running"
        assert status.exists is True
        assert status.needs_preparation is False
        assert status.preparation_actions == []
    
    def test_inspect_docker_containers_stopped(self):
        """Test inspection of stopped Docker containers"""
        # Mock docker driver methods for stopped container
        self.mock_docker_driver.ps.return_value = ["/cph_python"]
        self.mock_docker_driver.inspect.return_value = {
            "State": {"Status": "exited"}
        }
        
        result = self.inspector.inspect_docker_containers(["cph_python"])
        
        assert "cph_python" in result
        status = result["cph_python"]
        assert status.current_state == "stopped"
        assert status.exists is True
        assert status.needs_preparation is True
        assert "remove_stopped_container" in status.preparation_actions
        assert "run_new_container" in status.preparation_actions
    
    def test_inspect_docker_containers_missing(self):
        """Test inspection of missing Docker containers"""
        # Mock docker driver methods for no containers
        self.mock_docker_driver.ps.return_value = []
        
        result = self.inspector.inspect_docker_containers(["cph_python"])
        
        assert "cph_python" in result
        status = result["cph_python"]
        assert status.current_state == "missing"
        assert status.exists is False
        assert status.needs_preparation is True
        assert status.preparation_actions == ["run_new_container"]
    
    def test_inspect_directories_exists(self):
        """Test inspection of existing directories"""
        # Mock file exists response
        mock_result = MagicMock(spec=FileResult)
        mock_result.success = True
        mock_result.exists = True
        self.mock_file_driver.execute.return_value = mock_result
        
        result = self.inspector.inspect_directories(["/workspace"])
        
        assert "/workspace" in result
        status = result["/workspace"]
        assert status.resource_type == ResourceType.DIRECTORY
        assert status.current_state == "exists"
        assert status.exists is True
        assert status.needs_preparation is False
        assert status.preparation_actions == []
    
    def test_inspect_directories_missing(self):
        """Test inspection of missing directories"""
        # Mock file exists response
        mock_result = MagicMock(spec=FileResult)
        mock_result.success = True
        mock_result.exists = False
        self.mock_file_driver.execute.return_value = mock_result
        
        result = self.inspector.inspect_directories(["/workspace"])
        
        assert "/workspace" in result
        status = result["/workspace"]
        assert status.current_state == "missing"
        assert status.exists is False
        assert status.needs_preparation is True
        assert status.preparation_actions == ["create_directory"]
    
    def test_extract_requirements_docker_exec(self):
        """Test extracting requirements from docker exec tasks"""
        workflow_tasks = [
            {
                "command": "docker exec cph_python python main.py",
                "request_type": "shell"
            }
        ]
        
        requirements = self.inspector.extract_requirements_from_workflow_tasks(workflow_tasks)
        
        assert len(requirements) == 1
        req = requirements[0]
        assert req.resource_type == ResourceType.DOCKER_CONTAINER
        assert req.identifier == "cph_python"
        assert req.required_state == "running"
        assert req.context_info["task_type"] == "docker_exec"
    
    def test_extract_requirements_docker_cp(self):
        """Test extracting requirements from docker cp tasks"""
        workflow_tasks = [
            {
                "command": "docker cp /local/file.py cph_python:/workspace/file.py",
                "request_type": "shell"
            }
        ]
        
        requirements = self.inspector.extract_requirements_from_workflow_tasks(workflow_tasks)
        
        # Should extract both container and directory requirements
        container_reqs = [r for r in requirements if r.resource_type == ResourceType.DOCKER_CONTAINER]
        directory_reqs = [r for r in requirements if r.resource_type == ResourceType.DIRECTORY]
        
        assert len(container_reqs) == 1
        assert container_reqs[0].identifier == "cph_python"
        assert container_reqs[0].required_state == "running"
        
        assert len(directory_reqs) == 1
        assert directory_reqs[0].identifier == "/workspace"
        assert directory_reqs[0].required_state == "exists"
    
    def test_extract_container_name_from_exec(self):
        """Test container name extraction from exec command"""
        task_data = {"command": "docker exec cph_python_abc123 python script.py"}
        
        container_name = self.inspector._extract_container_name_from_exec(task_data)
        
        assert container_name == "cph_python_abc123"
    
    def test_extract_container_name_from_cp(self):
        """Test container name extraction from cp command"""
        # Test copy TO container
        task_data = {"command": "docker cp /local/file cph_python:/remote/file"}
        container_name = self.inspector._extract_container_name_from_cp(task_data)
        assert container_name == "cph_python"
        
        # Test copy FROM container
        task_data = {"command": "docker cp cph_python:/remote/file /local/file"}
        container_name = self.inspector._extract_container_name_from_cp(task_data)
        assert container_name == "cph_python"
    
    def test_extract_destination_directory_from_cp(self):
        """Test destination directory extraction from cp command"""
        # Test copy TO container
        task_data = {"command": "docker cp /local/file cph_python:/workspace/subdir/file"}
        dest_dir = self.inspector._extract_destination_directory_from_cp(task_data)
        assert dest_dir == "/workspace/subdir"
        
        # Test copy FROM container to local
        task_data = {"command": "docker cp cph_python:/remote/file /local/output/file"}
        dest_dir = self.inspector._extract_destination_directory_from_cp(task_data)
        assert dest_dir == "/local/output"