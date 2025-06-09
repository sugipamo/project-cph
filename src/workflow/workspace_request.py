"""Workspace operation request - simplified replacement for FilePreparationRequest."""
from typing import Any, Optional

from src.domain.constants.operation_type import OperationType
from src.domain.requests.base.base_request import BaseRequest


class WorkspaceRequest(BaseRequest):
    """Request for workspace operations using ProblemWorkspaceService.

    Replaces the complex FilePreparationRequest/StateTransition system
    with direct service calls.
    """

    def __init__(
        self,
        operation_type: str,
        contest: str,
        problem: str,
        language: str,
        force: bool = False,
        allow_failure: bool = False,
        name: Optional[str] = None
    ):
        """Initialize workspace request.

        Args:
            operation_type: Type of operation ('workspace_switch', 'move_test_files', etc.)
            contest: Contest name (e.g. "abc300")
            problem: Problem name (e.g. "a")
            language: Language name (e.g. "python")
            force: Force operation even if already in target state
            allow_failure: Allow operation to fail without stopping execution
            name: Optional request name for logging
        """
        super().__init__(name=name or f"{operation_type}_{contest}_{problem}")
        self.allow_failure = allow_failure
        self._operation_type = OperationType.WORKSPACE
        self.workspace_operation = operation_type  # Specific workspace operation type
        self.contest = contest
        self.problem = problem
        self.language = language
        self.force = force

    @property
    def operation_type(self) -> OperationType:
        """Return the operation type of this request."""
        return self._operation_type

    def _execute_core(self, driver: Optional[Any]) -> Any:
        """Core execution logic using workspace driver.

        Args:
            driver: WorkspaceDriver instance

        Returns:
            Execution result from the workspace service
        """
        if driver is None:
            raise ValueError("WorkspaceRequest requires a driver")

        # The driver should be a WorkspaceDriver that knows how to handle this request
        return driver.execute(self)

    def __str__(self) -> str:
        return f"WorkspaceRequest({self.workspace_operation}: {self.contest}/{self.problem} in {self.language})"

    def __repr__(self) -> str:
        return (f"WorkspaceRequest(workspace_operation='{self.workspace_operation}', "
                f"contest='{self.contest}', problem='{self.problem}', "
                f"language='{self.language}', force={self.force}, "
                f"allow_failure={self.allow_failure})")
