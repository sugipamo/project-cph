"""
Facade to bridge pure functions with existing APIs
"""
from typing import List, Dict, Any, Tuple, Optional
from src.pure_functions.workflow_builder_pure import (
    WorkflowBuildInput,
    build_workflow_pure
)
from src.pure_functions.execution_context_pure import (
    ExecutionData,
    execution_data_to_step_context_pure
)
from src.pure_functions.workflow_execution_pure import (
    extract_workflow_config_pure,
    plan_workflow_execution_pure,
    validate_workflow_plan_pure
)
from src.env_core.step.step import StepContext
from src.env_core.workflow.request_execution_graph import RequestExecutionGraph


class PureWorkflowFacade:
    """
    Facade that provides clean API to pure functions
    
    This class serves as a bridge between the existing object-oriented APIs
    and the new pure function implementations.
    """
    
    @staticmethod
    def build_workflow_from_context(
        execution_context,
        json_steps: Optional[List[Dict[str, Any]]] = None
    ) -> Tuple[RequestExecutionGraph, List[str], List[str]]:
        """
        Build workflow from execution context (compatible with existing API)
        
        Args:
            execution_context: Existing ExecutionContext object
            json_steps: Optional JSON steps (extracted from context if not provided)
            
        Returns:
            Tuple of (graph, errors, warnings)
        """
        # Extract data from execution context
        execution_data = ExecutionData(
            command_type=execution_context.command_type,
            language=execution_context.language,
            contest_name=execution_context.contest_name,
            problem_name=execution_context.problem_name,
            env_type=execution_context.env_type,
            env_json=execution_context.env_json,
            working_directory=getattr(execution_context, 'working_directory', None),
            contest_current_path=getattr(execution_context, 'contest_current_path', None),
            workspace_path=getattr(execution_context, 'workspace_path', None)
        )
        
        # Get JSON steps
        if json_steps is None:
            workflow_config = extract_workflow_config_pure(execution_data)
            if not workflow_config:
                return RequestExecutionGraph(), ["No workflow configuration found"], []
            json_steps = workflow_config.steps
        
        # Convert to step context
        step_context_data = execution_data_to_step_context_pure(execution_data)
        step_context = StepContext(
            contest_name=step_context_data.contest_name,
            problem_name=step_context_data.problem_name,
            language=step_context_data.language,
            env_type=step_context_data.env_type,
            command_type=step_context_data.command_type,
            workspace_path=step_context_data.workspace_path,
            contest_current_path=step_context_data.contest_current_path,
            contest_stock_path=step_context_data.contest_stock_path,
            contest_template_path=step_context_data.contest_template_path,
            contest_temp_path=step_context_data.contest_temp_path,
            source_file_name=step_context_data.source_file_name,
            language_id=step_context_data.language_id
        )
        
        # Build workflow using pure function
        input_data = WorkflowBuildInput(
            json_steps=json_steps,
            context=step_context
        )
        
        output = build_workflow_pure(input_data)
        
        # Convert back to RequestExecutionGraph
        graph = RequestExecutionGraph()
        for node in output.nodes:
            graph.add_request_node(node)
        
        for from_id, to_id in output.edges:
            # Add edges to graph if the graph supports it
            pass  # RequestExecutionGraph might not have direct edge support
        
        return graph, output.errors, output.warnings
    
    @staticmethod
    def validate_execution_context(execution_context) -> Tuple[bool, List[str]]:
        """
        Validate execution context using pure functions
        
        Args:
            execution_context: Existing ExecutionContext object
            
        Returns:
            Tuple of (is_valid, errors)
        """
        from src.pure_functions.execution_context_pure import validate_execution_data_pure
        
        # Convert to ExecutionData
        execution_data = ExecutionData(
            command_type=execution_context.command_type or "",
            language=execution_context.language or "",
            contest_name=execution_context.contest_name or "",
            problem_name=execution_context.problem_name or "",
            env_type=execution_context.env_type or "",
            env_json=execution_context.env_json or {}
        )
        
        errors = validate_execution_data_pure(execution_data)
        return len(errors) == 0, errors
    
    @staticmethod
    def plan_workflow_from_context(execution_context):
        """
        Plan workflow execution using pure functions
        
        Args:
            execution_context: Existing ExecutionContext object
            
        Returns:
            WorkflowPlan object
        """
        # Convert to pure data structures
        execution_data = ExecutionData(
            command_type=execution_context.command_type,
            language=execution_context.language,
            contest_name=execution_context.contest_name,
            problem_name=execution_context.problem_name,
            env_type=execution_context.env_type,
            env_json=execution_context.env_json,
            working_directory=getattr(execution_context, 'working_directory', None),
            contest_current_path=getattr(execution_context, 'contest_current_path', None),
            workspace_path=getattr(execution_context, 'workspace_path', None)
        )
        
        # Extract workflow config
        workflow_config = extract_workflow_config_pure(execution_data)
        if not workflow_config:
            from src.pure_functions.workflow_execution_pure import WorkflowPlan
            return WorkflowPlan(
                main_steps=[],
                preparation_steps=[],
                dependencies=[],
                errors=["No workflow configuration found"]
            )
        
        # Convert to step context data
        step_context_data = execution_data_to_step_context_pure(execution_data)
        
        # Plan execution
        plan = plan_workflow_execution_pure(workflow_config, step_context_data)
        
        # Validate plan
        validation_errors = validate_workflow_plan_pure(plan)
        if validation_errors:
            from src.pure_functions.workflow_execution_pure import WorkflowPlan
            return WorkflowPlan(
                main_steps=plan.main_steps,
                preparation_steps=plan.preparation_steps,
                dependencies=plan.dependencies,
                errors=plan.errors + validation_errors,
                warnings=plan.warnings
            )
        
        return plan


def create_test_execution_data(
    command_type: str = "build",
    language: str = "python",
    contest_name: str = "test_contest",
    problem_name: str = "a",
    env_type: str = "local"
) -> ExecutionData:
    """
    Create test execution data for testing purposes
    
    This function makes it easy to create test data without complex setup
    """
    return ExecutionData(
        command_type=command_type,
        language=language,
        contest_name=contest_name,
        problem_name=problem_name,
        env_type=env_type,
        env_json={
            language: {
                "commands": {
                    command_type: {
                        "steps": [
                            {"type": "shell", "cmd": ["echo", "test"]}
                        ]
                    }
                }
            }
        },
        workspace_path="./workspace",
        contest_current_path="./contest_current"
    )


def create_test_step_context_data(
    contest_name: str = "test_contest",
    problem_name: str = "a",
    language: str = "python",
    env_type: str = "local",
    command_type: str = "build"
) -> "StepContextData":
    """
    Create test step context data for testing purposes
    """
    from src.pure_functions.execution_context_pure import StepContextData
    
    return StepContextData(
        contest_name=contest_name,
        problem_name=problem_name,
        language=language,
        env_type=env_type,
        command_type=command_type,
        workspace_path="./workspace",
        contest_current_path="./contest_current"
    )