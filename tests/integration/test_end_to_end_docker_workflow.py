"""
End-to-end integration test for Docker workflow with fitting
"""
import pytest
from unittest.mock import MagicMock, patch, call

from src.env_core.step.step import Step, StepType
from src.env_core.workflow.pure_request_factory import PureRequestFactory
from src.env_core.workflow.graph_based_workflow_builder import GraphBasedWorkflowBuilder
from src.env_core.workflow.request_execution_graph import RequestExecutionGraph
from src.env_integration.fitting.preparation_executor import PreparationExecutor
from src.context.execution_context import ExecutionContext


class TestEndToEndDockerWorkflow:
    """End-to-end test for complete Docker workflow with fitting preparation"""
    
    def setup_method(self):
        """Setup comprehensive test environment"""
        # Mock operations
        self.mock_operations = MagicMock()
        self.mock_docker_driver = MagicMock()
        self.mock_file_driver = MagicMock()
        
        self.mock_operations.resolve.side_effect = lambda driver_type: {
            "docker_driver": self.mock_docker_driver,
            "file_driver": self.mock_file_driver
        }[driver_type]
        
        # Mock context with realistic values
        self.mock_context = MagicMock(spec=ExecutionContext)
        self.mock_context.get_docker_names.return_value = {
            "image_name": "python_abc123",
            "container_name": "cph_python_abc123",
            "oj_image_name": "ojtools_def456",
            "oj_container_name": "cph_ojtools_def456"
        }
        self.mock_context.language = "python"
        self.mock_context.contest_name = "abc300"
        self.mock_context.problem_name = "a"
        self.mock_context.env_type = "docker"
        
        # Setup dockerfile_resolver properly
        mock_dockerfile_resolver = MagicMock()
        mock_dockerfile_resolver.dockerfile = "FROM python:3.9\nRUN pip install requests"
        mock_dockerfile_resolver.oj_dockerfile = None
        self.mock_context.dockerfile_resolver = mock_dockerfile_resolver
        
        # Components
        self.preparation_executor = PreparationExecutor(self.mock_operations, self.mock_context)
        self.workflow_builder = GraphBasedWorkflowBuilder()
    
    def test_complete_competitive_programming_workflow(self):
        """Test complete workflow: prepare environment, copy code, execute, get results"""
        
        # Define a realistic competitive programming workflow
        workflow_json = [
            {
                "type": "mkdir",
                "cmd": ["/tmp/workspace"]
            },
            {
                "type": "docker_cp", 
                "cmd": ["/tmp/workspace/main.py", "cph_python_abc123:/app/main.py"]
            },
            {
                "type": "docker_cp",
                "cmd": ["/tmp/workspace/input.txt", "cph_python_abc123:/app/input.txt"]
            },
            {
                "type": "docker_exec",
                "cmd": ["cph_python_abc123", "python", "/app/main.py", "<", "/app/input.txt"]
            },
            {
                "type": "docker_cp",
                "cmd": ["cph_python_abc123:/app/output.txt", "/tmp/workspace/output.txt"]
            }
        ]
        
        # Mock environment state - clean slate
        self.mock_docker_driver.ps.return_value = []  # No containers
        
        # Mock file operations
        mock_file_result = MagicMock()
        mock_file_result.success = True
        mock_file_result.exists = False  # Directories need creation
        self.mock_file_driver.execute.return_value = mock_file_result
        
        # Step 1: Convert JSON to Steps
        workflow_steps = []
        for step_json in workflow_json:
            step = Step(
                type=StepType(step_json["type"]),
                cmd=step_json["cmd"],
                show_output=True
            )
            workflow_steps.append(step)
        
        # Step 2: Convert Steps to Requests
        workflow_requests = []
        workflow_tasks = []
        for step in workflow_steps:
            request = PureRequestFactory.create_request_from_step(step, self.mock_context)
            if request:
                workflow_requests.append(request)
                
                # Create task representation for fitting analysis
                if step.type.value.startswith("docker"):
                    command = f"docker {step.type.value.split('_')[1]} {' '.join(step.cmd)}"
                else:
                    command = f"{step.type.value} {' '.join(step.cmd)}"
                
                workflow_tasks.append({
                    "request_object": request,
                    "command": command,
                    "request_type": "docker" if step.type.value.startswith("docker") else "file"
                })
        
        # Step 3: Analyze environment and generate preparation tasks
        preparation_tasks, environment_statuses = self.preparation_executor.analyze_and_prepare(workflow_tasks)
        
        # Verify preparation tasks were generated
        assert len(preparation_tasks) > 0
        
        # Should have Docker container preparation
        docker_tasks = [t for t in preparation_tasks if t.task_type == "docker_run"]
        assert len(docker_tasks) == 1
        assert docker_tasks[0].request_object.container == "cph_python_abc123"
        
        # Should have directory preparation
        mkdir_tasks = [t for t in preparation_tasks if t.task_type == "mkdir"]
        assert len(mkdir_tasks) >= 1
        
        # Step 4: Convert preparation tasks to requests
        preparation_requests = self.preparation_executor.convert_to_workflow_requests(preparation_tasks)
        
        # Step 5: Combine preparation and workflow requests
        all_requests = preparation_requests + workflow_requests
        
        # Step 6: Create execution graph
        from src.env_core.workflow.request_execution_graph import RequestNode
        execution_graph = RequestExecutionGraph()
        
        # Add all requests to graph
        for i, request in enumerate(all_requests):
            request_id = f"request_{i:03d}"
            node = RequestNode(request_id, request)
            execution_graph.add_request_node(node)
        
        # Step 7: Get execution order (topological sort)
        execution_order = execution_graph.get_execution_order()
        
        # Verify execution order makes sense
        assert len(execution_order) == len(all_requests)
        
        # Step 8: Get parallel execution groups
        parallel_groups = execution_graph.get_parallel_groups()
        
        # Verify we can execute some tasks in parallel
        # (preparation tasks should be able to run in parallel)
        total_parallel_tasks = sum(len(group) for group in parallel_groups)
        assert total_parallel_tasks == len(all_requests)
        
        # Verify the workflow covers the complete competitive programming cycle
        request_types = [type(req).__name__ for req in all_requests]
        
        # Should include Docker operations
        assert any("DockerRequest" in req_type for req_type in request_types)
        
        # Should include file operations  
        assert any("FileRequest" in req_type for req_type in request_types)
    
    def test_oj_tools_integration_workflow(self):
        """Test workflow integration with online-judge-tools"""
        
        # OJ tools workflow
        workflow_json = [
            {
                "type": "docker_exec",
                "cmd": ["cph_ojtools_def456", "oj", "download", "https://atcoder.jp/contests/abc300/tasks/abc300_a"]
            },
            {
                "type": "docker_cp",
                "cmd": ["/tmp/main.py", "cph_ojtools_def456:/app/main.py"]
            },
            {
                "type": "docker_exec", 
                "cmd": ["cph_ojtools_def456", "oj", "test", "-c", "python3 /app/main.py"]
            }
        ]
        
        # Mock environment - OJ container missing
        self.mock_docker_driver.ps.return_value = []
        
        # Convert to steps and requests
        workflow_steps = []
        workflow_tasks = []
        
        for step_json in workflow_json:
            step = Step(
                type=StepType(step_json["type"]),
                cmd=step_json["cmd"],
                show_output=True
            )
            workflow_steps.append(step)
            
            request = PureRequestFactory.create_request_from_step(step, self.mock_context)
            workflow_tasks.append({
                "request_object": request,
                "command": f"docker {step.type.value.split('_')[1]} {' '.join(step.cmd)}",
                "request_type": "docker"
            })
        
        # Analyze and prepare
        preparation_tasks, statuses = self.preparation_executor.analyze_and_prepare(workflow_tasks)
        
        # Should prepare OJ tools container
        docker_tasks = [t for t in preparation_tasks if t.task_type == "docker_run"]
        assert len(docker_tasks) == 1
        
        oj_task = docker_tasks[0]
        assert oj_task.request_object.container == "cph_ojtools_def456"
        assert oj_task.request_object.image == "ojtools_def456"
        assert "ojtools" in oj_task.description.lower()
    
    def test_error_recovery_workflow(self):
        """Test workflow with error conditions and recovery"""
        
        # Workflow that might encounter errors
        workflow_json = [
            {
                "type": "docker_exec",
                "cmd": ["cph_python_abc123", "python", "--version"]
            },
            {
                "type": "docker_exec", 
                "cmd": ["cph_python_abc123", "python", "-c", "import nonexistent_module"]  # This will fail
            },
            {
                "type": "docker_exec",
                "cmd": ["cph_python_abc123", "echo", "recovery step"]
            }
        ]
        
        # Mock environment - container stopped (needs recovery)
        self.mock_docker_driver.ps.return_value = ["/cph_python_abc123"]
        self.mock_docker_driver.inspect.return_value = {
            "State": {"Status": "exited"}
        }
        
        # Convert to workflow
        workflow_tasks = []
        for step_json in workflow_json:
            step = Step(
                type=StepType(step_json["type"]),
                cmd=step_json["cmd"],
                allow_failure=(step_json["cmd"][1] == "python" and "nonexistent" in step_json["cmd"][2])  # Allow second step to fail
            )
            
            request = PureRequestFactory.create_request_from_step(step, self.mock_context)
            workflow_tasks.append({
                "request_object": request,
                "command": f"docker exec {' '.join(step.cmd)}",
                "request_type": "docker"
            })
        
        # Analyze and prepare
        preparation_tasks, statuses = self.preparation_executor.analyze_and_prepare(workflow_tasks)
        
        # Should generate recovery tasks (remove stopped container, run new one)
        remove_tasks = [t for t in preparation_tasks if t.task_type == "docker_remove"]
        run_tasks = [t for t in preparation_tasks if t.task_type == "docker_run"]
        
        assert len(remove_tasks) == 1
        assert len(run_tasks) == 1
        
        # Check dependency ordering
        run_task = run_tasks[0]
        remove_task = remove_tasks[0]
        assert remove_task.task_id in run_task.dependencies
        
        # Verify status indicates stopped container needing preparation
        container_status = statuses["cph_python_abc123"]
        assert container_status.current_state == "stopped"
        assert container_status.needs_preparation is True
        assert "remove_stopped_container" in container_status.preparation_actions
        assert "run_new_container" in container_status.preparation_actions
    
    def test_performance_optimization_workflow(self):
        """Test workflow optimized for performance with parallel execution"""
        
        # Workflow designed for parallel execution
        workflow_json = [
            # These can run in parallel (different directories)
            {
                "type": "mkdir",
                "cmd": ["/tmp/workspace1"]
            },
            {
                "type": "mkdir", 
                "cmd": ["/tmp/workspace2"]
            },
            {
                "type": "mkdir",
                "cmd": ["/tmp/workspace3"]
            },
            # These depend on directories being created
            {
                "type": "docker_cp",
                "cmd": ["/tmp/workspace1/file1.py", "cph_python_abc123:/app/file1.py"]
            },
            {
                "type": "docker_cp",
                "cmd": ["/tmp/workspace2/file2.py", "cph_python_abc123:/app/file2.py"]
            }
        ]
        
        # Mock environment - container missing, directories missing  
        self.mock_docker_driver.ps.return_value = []
        
        mock_file_result = MagicMock()
        mock_file_result.success = True
        mock_file_result.exists = False
        self.mock_file_driver.execute.return_value = mock_file_result
        
        # Convert to workflow
        workflow_tasks = []
        for step_json in workflow_json:
            step = Step(
                type=StepType(step_json["type"]),
                cmd=step_json["cmd"]
            )
            
            request = PureRequestFactory.create_request_from_step(step, self.mock_context)
            
            if step.type.value.startswith("docker"):
                command = f"docker {step.type.value.split('_')[1]} {' '.join(step.cmd)}"
            else:
                command = f"{step.type.value} {' '.join(step.cmd)}"
                
            workflow_tasks.append({
                "request_object": request,
                "command": command,
                "request_type": "docker" if step.type.value.startswith("docker") else "file"
            })
        
        # Analyze and prepare
        preparation_tasks, statuses = self.preparation_executor.analyze_and_prepare(workflow_tasks)
        
        # Should generate multiple mkdir tasks that can run in parallel
        mkdir_tasks = [t for t in preparation_tasks if t.task_type == "mkdir"]
        docker_tasks = [t for t in preparation_tasks if t.task_type == "docker_run"]
        
        # Should have directory preparations (may be consolidated)
        assert len(mkdir_tasks) >= 1  # For the directories needed by docker cp
        
        # Should have Docker container preparation
        assert len(docker_tasks) == 1
        
        # Check parallel groups
        mkdir_parallel_tasks = [t for t in mkdir_tasks if t.parallel_group == "mkdir_preparation"]
        docker_parallel_tasks = [t for t in docker_tasks if t.parallel_group == "docker_preparation"]
        
        # mkdir and docker tasks should be in different parallel groups
        assert len(mkdir_parallel_tasks) >= 1
        assert len(docker_parallel_tasks) >= 1
        
        # Convert to requests and verify performance characteristics
        preparation_requests = self.preparation_executor.convert_to_workflow_requests(preparation_tasks)
        
        # Should be able to execute tasks in parallel
        assert len(preparation_requests) >= 2  # At least container and directory preparation