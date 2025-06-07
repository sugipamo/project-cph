"""
Complete End-to-End Workflow Execution Demo

This example demonstrates how to:
1. Define workflow steps as JSON
2. Convert JSON steps to executable workflows using GraphBasedWorkflowBuilder
3. Execute workflows with dependency management
4. Handle fitting (environment preparation)
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.env_core.workflow.graph_based_workflow_builder import GraphBasedWorkflowBuilder
from src.env_core.step.step import StepContext
from src.env_integration.fitting.preparation_executor import PreparationExecutor
from src.infrastructure.di_container import DIContainer
from src.infrastructure.mock.mock_docker_driver import MockDockerDriver
from src.infrastructure.mock.mock_file_driver import MockFileDriver
from src.infrastructure.mock.mock_shell_driver import MockShellDriver
from unittest.mock import MagicMock


def demonstrate_simple_workflow():
    """Demonstrate a simple file operation workflow"""
    print("=== Simple File Operations Workflow ===\n")
    
    # 1. Define workflow as JSON steps
    json_steps = [
        {
            "type": "mkdir",
            "cmd": ["/tmp/demo_project"]
        },
        {
            "type": "mkdir", 
            "cmd": ["/tmp/demo_project/src"]
        },
        {
            "type": "touch",
            "cmd": ["/tmp/demo_project/src/main.py"]
        },
        {
            "type": "copy",
            "cmd": ["/tmp/demo_project/src/main.py", "/tmp/demo_project/src/backup.py"]
        }
    ]
    
    print("1. JSON Workflow Definition:")
    for i, step in enumerate(json_steps):
        print(f"   Step {i+1}: {step['type']} {' '.join(step['cmd'])}")
    print()
    
    # 2. Create context (pure, no operations needed)
    context = StepContext(
        contest_name="demo",
        problem_name="example",
        language="python",
        env_type="local",
        command_type="run",
        workspace_path="/tmp/workspace",
        contest_current_path="/tmp/contest_current"
    )
    
    # 3. Build workflow graph from JSON
    builder = GraphBasedWorkflowBuilder.from_context(context)
    graph, errors, warnings = builder.build_graph_from_json_steps(json_steps)
    
    print("2. Workflow Graph Generation:")
    print(f"   Nodes: {len(graph.nodes)}")
    print(f"   Dependencies: {len(graph.edges)}")
    print(f"   Errors: {errors}")
    print(f"   Warnings: {warnings}")
    print()
    
    # 4. Analyze execution order
    try:
        execution_order = graph.get_execution_order()
        print("3. Execution Order (Topological Sort):")
        for i, node_id in enumerate(execution_order):
            node = graph.nodes[node_id]
            print(f"   {i+1}. {node_id}: {type(node.request).__name__}")
    except ValueError as e:
        print(f"   Error: {e}")
    print()
    
    # 5. Get parallel execution groups
    parallel_groups = graph.get_parallel_groups()
    print("4. Parallel Execution Groups:")
    for i, group in enumerate(parallel_groups):
        print(f"   Group {i+1}: {', '.join(group)} (can run in parallel)")
    print()
    
    return graph


def demonstrate_docker_workflow():
    """Demonstrate a Docker-based competitive programming workflow"""
    print("\n=== Docker Competitive Programming Workflow ===\n")
    
    # 1. Define a realistic CP workflow
    json_steps = [
        {
            "type": "docker_exec",
            "cmd": ["cph_python_abc300", "mkdir", "-p", "/app/workspace"]
        },
        {
            "type": "docker_cp",
            "cmd": ["./main.py", "cph_python_abc300:/app/workspace/main.py"]
        },
        {
            "type": "docker_cp",
            "cmd": ["./input.txt", "cph_python_abc300:/app/workspace/input.txt"]
        },
        {
            "type": "docker_exec",
            "cmd": ["cph_python_abc300", "python", "/app/workspace/main.py", "<", "/app/workspace/input.txt"]
        },
        {
            "type": "docker_cp",
            "cmd": ["cph_python_abc300:/app/workspace/output.txt", "./output.txt"]
        }
    ]
    
    print("1. Docker Workflow Steps:")
    for i, step in enumerate(json_steps):
        print(f"   Step {i+1}: {step['type']} {' '.join(step['cmd'])}")
    print()
    
    # 2. Create context with Docker information
    context = MagicMock()
    context.get_docker_names.return_value = {
        "image_name": "python_abc300",
        "container_name": "cph_python_abc300"
    }
    
    # 3. Build workflow
    builder = GraphBasedWorkflowBuilder.from_context(context)
    graph, errors, warnings = builder.build_graph_from_json_steps(json_steps)
    
    print("2. Docker Workflow Graph:")
    print(f"   Nodes: {len(graph.nodes)}")
    print(f"   Errors: {errors}")
    print()
    
    # 4. Show dependencies
    print("3. Dependencies:")
    for edge in graph.edges:
        from_node = graph.nodes[edge.from_node]
        to_node = graph.nodes[edge.to_node]
        print(f"   {edge.from_node} -> {edge.to_node}")
        print(f"      Type: {edge.dependency_type.value}")
        if edge.resource_path:
            print(f"      Resource: {edge.resource_path}")
    print()
    
    return graph


def demonstrate_workflow_with_fitting():
    """Demonstrate workflow with environment fitting/preparation"""
    print("\n=== Workflow with Environment Fitting ===\n")
    
    # 1. Setup mock environment
    mock_operations = MagicMock()
    mock_docker_driver = MockDockerDriver()
    mock_file_driver = MockFileDriver()
    
    mock_operations.resolve.side_effect = lambda driver_type: {
        "docker_driver": mock_docker_driver,
        "file_driver": mock_file_driver
    }[driver_type]
    
    # Mock context
    mock_context = MagicMock()
    mock_context.get_docker_names.return_value = {
        "image_name": "python_abc300",
        "container_name": "cph_python_abc300"
    }
    mock_context.language = "python"
    mock_context.contest_name = "abc300"
    mock_context.problem_name = "a"
    
    # 2. Define workflow that needs preparation
    workflow_json = [
        {
            "type": "mkdir",
            "cmd": ["/tmp/workspace"]
        },
        {
            "type": "docker_exec",
            "cmd": ["cph_python_abc300", "python", "--version"]
        }
    ]
    
    print("1. Workflow requiring preparation:")
    for step in workflow_json:
        print(f"   - {step['type']}: {' '.join(step['cmd'])}")
    print()
    
    # 3. Convert to workflow tasks
    from src.env_core.step.step import Step, StepType
    from src.env_core.workflow.request_factory_v2 import RequestFactoryV2
    
    workflow_tasks = []
    for step_json in workflow_json:
        step = Step(
            type=StepType(step_json["type"]),
            cmd=step_json["cmd"]
        )
        factory = RequestFactoryV2(mock_context)
        request = factory.create_request(step)
        
        task_type = "docker" if step_json["type"].startswith("docker") else "file"
        workflow_tasks.append({
            "request_object": request,
            "command": f"{step_json['type']} {' '.join(step_json['cmd'])}",
            "request_type": task_type
        })
    
    # 4. Analyze and prepare environment
    preparation_executor = PreparationExecutor(mock_operations, mock_context)
    
    # Mock environment state - container missing
    mock_docker_driver.ps.return_value = []  # No containers running
    
    preparation_tasks, environment_statuses = preparation_executor.analyze_and_prepare(workflow_tasks)
    
    print("2. Environment Analysis:")
    print(f"   Found {len(preparation_tasks)} preparation tasks needed:")
    for task in preparation_tasks:
        print(f"   - {task.task_type}: {task.description}")
    print()
    
    print("3. Environment Status:")
    for container, status in environment_statuses.items():
        print(f"   Container: {container}")
        print(f"   - Current state: {status.current_state}")
        print(f"   - Needs preparation: {status.needs_preparation}")
        if status.preparation_actions:
            print(f"   - Actions: {', '.join(status.preparation_actions)}")
    print()
    
    # 5. Convert preparation tasks to executable requests
    preparation_requests = preparation_executor.convert_to_workflow_requests(preparation_tasks)
    
    print("4. Generated Preparation Requests:")
    for i, req in enumerate(preparation_requests):
        print(f"   {i+1}. {type(req).__name__}")
    
    return preparation_tasks, workflow_tasks


def demonstrate_complete_execution():
    """Demonstrate complete workflow execution with mock drivers"""
    print("\n=== Complete Workflow Execution ===\n")
    
    # 1. Create a simple workflow
    json_steps = [
        {"type": "shell", "cmd": ["echo", "Starting workflow..."]},
        {"type": "shell", "cmd": ["echo", "Processing..."]},
        {"type": "shell", "cmd": ["echo", "Complete!"]}
    ]
    
    # 2. Build graph
    context = StepContext(
        contest_name="demo",
        problem_name="example", 
        language="python",
        env_type="local",
        command_type="run",
        workspace_path="/tmp/workspace",
        contest_current_path="/tmp/contest_current"
    )
    
    builder = GraphBasedWorkflowBuilder.from_context(context)
    graph, _, _ = builder.build_graph_from_json_steps(json_steps)
    
    # 3. Execute with mock driver
    mock_driver = MockShellDriver()
    
    print("1. Sequential Execution:")
    results = graph.execute_sequential(driver=mock_driver)
    
    for i, result in enumerate(results):
        print(f"   Step {i+1}: {'Success' if result.success else 'Failed'}")
        if hasattr(result, 'output') and result.output:
            print(f"   Output: {result.output}")
    
    print("\n2. Parallel Execution:")
    # Reset node states
    for node in graph.nodes.values():
        node.status = "pending"
        node.result = None
    
    results = graph.execute_parallel(driver=mock_driver, max_workers=2)
    
    for i, result in enumerate(results):
        print(f"   Step {i+1}: {'Success' if result.success else 'Failed'}")
    
    return results


def main():
    """Run all demonstrations"""
    print("=" * 60)
    print("Complete End-to-End Workflow Execution Examples")
    print("=" * 60)
    
    # 1. Simple file operations
    graph1 = demonstrate_simple_workflow()
    
    # 2. Docker workflow
    graph2 = demonstrate_docker_workflow()
    
    # 3. Workflow with fitting
    prep_tasks, workflow_tasks = demonstrate_workflow_with_fitting()
    
    # 4. Complete execution
    results = demonstrate_complete_execution()
    
    print("\n" + "=" * 60)
    print("Summary:")
    print("- JSON steps are converted to Step objects")
    print("- Steps are converted to Request objects (pure, no operations)")
    print("- Requests are organized into a dependency graph")
    print("- Graph can be executed sequentially or in parallel")
    print("- Fitting analyzes environment and prepares as needed")
    print("=" * 60)


if __name__ == "__main__":
    main()