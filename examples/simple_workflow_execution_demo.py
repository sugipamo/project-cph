#!/usr/bin/env python3
"""
Simple Workflow Execution Demo

This example demonstrates the key concepts of executing workflows end-to-end:
1. JSON steps → Step objects → Request objects
2. Building dependency graphs
3. Executing workflows
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.env_core.workflow.graph_based_workflow_builder import GraphBasedWorkflowBuilder
from src.env_core.step.step import StepContext, Step, StepType
from src.env_core.workflow.pure_request_factory import PureRequestFactory


def main():
    print("=" * 70)
    print("WORKFLOW EXECUTION: From JSON to Execution")
    print("=" * 70)
    print()

    # ========================================================================
    # STEP 1: Define workflow as JSON
    # ========================================================================
    print("STEP 1: Define Workflow as JSON")
    print("-" * 40)
    
    json_steps = [
        {
            "type": "mkdir",
            "cmd": ["./workspace"]
        },
        {
            "type": "mkdir", 
            "cmd": ["./workspace/src"]
        },
        {
            "type": "touch",
            "cmd": ["./workspace/src/main.py"]
        },
        {
            "type": "shell",
            "cmd": ["echo", "# Python code", ">", "./workspace/src/main.py"]
        },
        {
            "type": "copy",
            "cmd": ["./workspace/src/main.py", "./workspace/src/backup.py"]
        }
    ]
    
    print("JSON workflow definition:")
    for i, step in enumerate(json_steps):
        print(f"  {i+1}. {step['type']:10} {' '.join(step['cmd'])}")
    print()

    # ========================================================================
    # STEP 2: Create execution context
    # ========================================================================
    print("STEP 2: Create Execution Context")
    print("-" * 40)
    
    context = StepContext(
        contest_name="abc300",
        problem_name="a",
        language="python",
        env_type="local",
        command_type="run",
        workspace_path="./workspace",
        contest_current_path="./contest_current"
    )
    
    print(f"Context created:")
    print(f"  Contest: {context.contest_name}")
    print(f"  Problem: {context.problem_name}")
    print(f"  Language: {context.language}")
    print(f"  Environment: {context.env_type}")
    print()

    # ========================================================================
    # STEP 3: Build workflow graph from JSON
    # ========================================================================
    print("STEP 3: Build Workflow Graph")
    print("-" * 40)
    
    builder = GraphBasedWorkflowBuilder.from_context(context)
    graph, errors, warnings = builder.build_graph_from_json_steps(json_steps)
    
    print(f"Graph building results:")
    print(f"  Nodes created: {len(graph.nodes)}")
    print(f"  Dependencies: {len(graph.edges)}")
    print(f"  Errors: {len(errors)}")
    print(f"  Warnings: {len(warnings)}")
    
    if errors:
        print("\nErrors:")
        for error in errors:
            print(f"  - {error}")
    
    if warnings:
        print("\nWarnings:")
        for warning in warnings:
            print(f"  - {warning}")
    print()

    # ========================================================================
    # STEP 4: Show how JSON → Step → Request conversion works
    # ========================================================================
    print("STEP 4: Conversion Process (JSON → Step → Request)")
    print("-" * 40)
    
    # Take first JSON step as example
    example_json = json_steps[0]
    print(f"Example JSON step: {example_json}")
    
    # Convert to Step object
    example_step = Step(
        type=StepType(example_json["type"]),
        cmd=example_json["cmd"]
    )
    print(f"→ Step object: type={example_step.type}, cmd={example_step.cmd}")
    
    # Convert to Request object (pure function, no operations needed)
    example_request = PureRequestFactory.create_request_from_step(example_step)
    print(f"→ Request object: {type(example_request).__name__}")
    print(f"  - Operation: {example_request.op if hasattr(example_request, 'op') else 'N/A'}")
    print(f"  - Path: {example_request.path if hasattr(example_request, 'path') else 'N/A'}")
    print()

    # ========================================================================
    # STEP 5: Analyze execution order and dependencies
    # ========================================================================
    print("STEP 5: Execution Analysis")
    print("-" * 40)
    
    # Get topological sort (execution order)
    try:
        execution_order = graph.get_execution_order()
        print("Execution order (topological sort):")
        for i, node_id in enumerate(execution_order):
            node = graph.nodes[node_id]
            request_type = type(node.request).__name__
            print(f"  {i+1}. {node_id} ({request_type})")
    except ValueError as e:
        print(f"Error determining execution order: {e}")
    print()
    
    # Show dependencies
    if graph.edges:
        print("Dependencies:")
        for edge in graph.edges[:5]:  # Show first 5
            print(f"  {edge.from_node} → {edge.to_node}")
            print(f"    Type: {edge.dependency_type.value}")
            if edge.resource_path:
                print(f"    Resource: {edge.resource_path}")
        if len(graph.edges) > 5:
            print(f"  ... and {len(graph.edges) - 5} more dependencies")
    print()

    # ========================================================================
    # STEP 6: Show parallel execution groups
    # ========================================================================
    print("STEP 6: Parallel Execution Groups")
    print("-" * 40)
    
    parallel_groups = graph.get_parallel_groups()
    print(f"Found {len(parallel_groups)} execution groups:")
    
    for i, group in enumerate(parallel_groups):
        print(f"\nGroup {i+1} (can run in parallel):")
        for node_id in group:
            node = graph.nodes[node_id]
            print(f"  - {node_id}: {type(node.request).__name__}")
    print()

    # ========================================================================
    # STEP 7: Demonstrate execution (conceptual)
    # ========================================================================
    print("STEP 7: Execution Methods")
    print("-" * 40)
    
    print("The graph can be executed in two ways:")
    print()
    print("1. Sequential Execution:")
    print("   graph.execute_sequential(driver=driver)")
    print("   - Executes nodes one by one in topological order")
    print("   - Respects all dependencies")
    print("   - Simpler but slower")
    print()
    print("2. Parallel Execution:")
    print("   graph.execute_parallel(driver=driver, max_workers=4)")
    print("   - Executes independent nodes concurrently")
    print("   - Uses thread pool for parallelism")
    print("   - Faster for workflows with parallelizable tasks")
    print()

    # ========================================================================
    # STEP 8: Docker workflow example
    # ========================================================================
    print("STEP 8: Docker Workflow Example")
    print("-" * 40)
    
    docker_steps = [
        {
            "type": "docker_exec",
            "cmd": ["my_container", "mkdir", "-p", "/app/test"]
        },
        {
            "type": "docker_cp",
            "cmd": ["./local_file.txt", "my_container:/app/test/file.txt"]
        },
        {
            "type": "docker_exec",
            "cmd": ["my_container", "cat", "/app/test/file.txt"]
        }
    ]
    
    print("Docker workflow steps:")
    for i, step in enumerate(docker_steps):
        print(f"  {i+1}. {step['type']:12} {' '.join(step['cmd'])}")
    print()
    
    # Show conversion of docker_exec step
    docker_step = Step(
        type=StepType.DOCKER_EXEC,
        cmd=["my_container", "echo", "Hello from Docker"]
    )
    docker_request = PureRequestFactory.create_request_from_step(docker_step)
    
    print("Docker step conversion:")
    print(f"  Step type: {docker_step.type}")
    print(f"  → Request type: {type(docker_request).__name__}")
    print(f"  → Container: {docker_request.container if hasattr(docker_request, 'container') else 'N/A'}")
    print(f"  → Command: {docker_request.command if hasattr(docker_request, 'command') else 'N/A'}")
    print()

    # ========================================================================
    # Summary
    # ========================================================================
    print("=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print()
    print("Complete workflow execution flow:")
    print("1. JSON steps (user input)")
    print("   ↓")
    print("2. Step objects (structured representation)")
    print("   ↓")
    print("3. Request objects (executable operations)")
    print("   ↓")
    print("4. RequestExecutionGraph (with dependencies)")
    print("   ↓")
    print("5. Execution (sequential or parallel)")
    print()
    print("Key points:")
    print("- Pure conversion: No operations/drivers needed until execution")
    print("- Dependency management: Automatic detection and ordering")
    print("- Parallel optimization: Independent tasks run concurrently")
    print("- Extensible: Easy to add new step types and operations")
    print()


if __name__ == "__main__":
    main()